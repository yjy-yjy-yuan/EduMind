"""
知识图谱和学习路径规划模块
1、实现功能：
    构建知识图谱
    生成个性化学习路径
    追踪学习进度
2、主要技术：
    使用知识图谱进行学习路径规划
    支持学习进度追踪"""

from typing import List, Dict, Tuple, Optional
import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from dataclasses import dataclass, field
import json
import os
from datetime import datetime
from py2neo import Graph, Node, Relationship
import spacy
from collections import defaultdict
import re
import sys

@dataclass
class KnowledgeNode:
    """知识点节点"""
    id: str
    content: str
    source_video: str
    timestamp: float
    entity_type: str
    difficulty: float = 0.5
    vector: Optional[np.ndarray] = None
    prerequisites: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)

class KnowledgeGraph:
    """知识图谱"""
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nodes = {}  # 存储所有节点
        self.graph = nx.DiGraph()  # 有向图
        self.node_embeddings = np.array([])
        self.node_ids = []
        self.index = None
        
        # 初始化NLP模型
        try:
            self.nlp = spacy.load("zh_core_web_sm")
            print("成功加载中文NLP模型")
        except OSError:
            print("尝试下载中文NLP模型...")
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "spacy", "download", "zh_core_web_sm"], 
                             check=True)
                self.nlp = spacy.load("zh_core_web_sm")
                print("成功下载并加载中文NLP模型")
            except Exception as e:
                print(f"无法加载中文NLP模型: {str(e)}")
                print("使用基础分词方式")
                self.nlp = None
        
        # 连接Neo4j数据库
        try:
            # 使用py2neo连接Neo4j
            self.neo4j_graph = Graph("neo4j://localhost:7687", auth=("neo4j", "cjx20040328"))
            print("Neo4j数据库连接成功！")
        except Exception as e:
            print(f"Neo4j连接失败: {str(e)}")
            self.neo4j_graph = None

    def extract_entities(self, text: str) -> List[Tuple[str, str, int, int]]:
        """使用NER提取实体"""
        entities = []
        
        if self.nlp:
            # 使用spaCy的NER
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append((ent.text, ent.label_, ent.start_char, ent.end_char))
        else:
            # 使用基础分词和规则
            words = text.split()
            current_pos = 0
            for word in words:
                if word.strip():
                    # 使用规则判断实体类型
                    entity_type = self._guess_entity_type(word)
                    if entity_type:
                        start_pos = text.find(word, current_pos)
                        end_pos = start_pos + len(word)
                        entities.append((word, entity_type, start_pos, end_pos))
                        current_pos = end_pos
        
        # 使用规则识别技术术语和概念
        tech_terms = self._identify_tech_terms(text)
        concepts = self._identify_concepts(text)
        
        entities.extend(tech_terms)
        entities.extend(concepts)
        
        return entities

    def _guess_entity_type(self, word: str) -> Optional[str]:
        """基于规则猜测实体类型"""
        if any(char.isdigit() for char in word):
            return 'NUMBER'
        if word.isupper():
            return 'ABBR'
        if word[0].isupper() and not word.isupper():
            return 'PROPER_NOUN'
        if len(word) > 1 and any(tech_suffix in word for tech_suffix in ['系统', '技术', '方法', '理论']):
            return 'TECH_TERM'
        return None

    def extract_relationships(self, text: str, entities: List[Tuple[str, str, int, int]]) -> List[Tuple[str, str, str]]:
        """提取实体间的关系"""
        relationships = []
        doc = self.nlp(text)
        
        # 基于依存句法分析的关系抽取
        for token in doc:
            if token.dep_ in ["prep", "compound", "amod"]:
                head = token.head.text
                child = token.text
                relationship = token.dep_
                relationships.append((head, relationship, child))
        
        # 基于模式匹配的关系抽取
        # 可以添加更多特定领域的关系抽取规则
        causal_relations = self._extract_causal_relations(text)
        hierarchical_relations = self._extract_hierarchical_relations(text)
        
        relationships.extend(causal_relations)
        relationships.extend(hierarchical_relations)
        
        return relationships

    def _identify_tech_terms(self, text: str) -> List[Tuple[str, str, int, int]]:
        """识别技术术语"""
        tech_terms = []
        # 技术术语的特征模式
        patterns = [
            r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b',  # 大写开头的词或词组
            r'\b[a-zA-Z]+\d+\b',  # 字母数字组合
            r'\b[A-Z][A-Z0-9]+\b',  # 纯大写字母或大写字母数字组合
            r'[\u4e00-\u9fa5]+(?:系统|框架|技术|算法|模型|方法|工具|平台|架构|协议|标准|接口|服务)',  # 中文技术术语
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group()
                tech_terms.append((term, 'TECH_TERM', match.start(), match.end()))
        
        return tech_terms

    def _identify_concepts(self, text: str) -> List[Tuple[str, str, int, int]]:
        """识别概念"""
        concepts = []
        # 概念的特征模式
        concept_patterns = [
            r'(?:概念|理论|原理|定义|规则|特征|性质|要素|机制|过程)[:：是为]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)',
            r'([\u4e00-\u9fa5a-zA-Z0-9]+)(?:指的是|表示|意味着|定义为)',
            r'所谓(?:的)?\s*([\u4e00-\u9fa5a-zA-Z0-9]+)',
        ]
        
        for pattern in concept_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                concept = match.group(1)
                concepts.append((concept, 'CONCEPT', match.start(1), match.end(1)))
        
        return concepts

    def _extract_causal_relations(self, text: str) -> List[Tuple[str, str, str]]:
        """提取因果关系"""
        causal_relations = []
        # 因果关系标记词
        causal_patterns = [
            (r'因为(.*?)所以(.*?)[。？！，,]', '因果关系'),
            (r'由于(.*?)导致(.*?)[。？！，,]', '因果关系'),
            (r'(.*?)是(.*?)的原因', '因果关系'),
            (r'(.*?)会造成(.*?)[。？！，,]', '因果关系'),
            (r'(.*?)引起(.*?)[。？！，,]', '因果关系'),
        ]
        
        for pattern, rel_type in causal_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) >= 2:
                    cause = match.group(1).strip()
                    effect = match.group(2).strip()
                    causal_relations.append((cause, rel_type, effect))
        
        return causal_relations

    def _extract_hierarchical_relations(self, text: str) -> List[Tuple[str, str, str]]:
        """提取层级关系"""
        hierarchical_relations = []
        # 层级关系标记词
        hierarchical_patterns = [
            (r'(.*?)包括(.*?)[。？！，,]', '包含关系'),
            (r'(.*?)属于(.*?)[。？！，,]', '从属关系'),
            (r'(.*?)是(.*?)的一种', '类型关系'),
            (r'(.*?)分为(.*?)[。？！，,]', '分类关系'),
            (r'(.*?)由(.*?)组成', '组成关系'),
        ]
        
        for pattern, rel_type in hierarchical_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) >= 2:
                    parent = match.group(1).strip()
                    child = match.group(2).strip()
                    # 对于逗号分隔的多个子项
                    for sub_child in re.split(r'[,，、]', child):
                        if sub_child.strip():
                            hierarchical_relations.append((parent, rel_type, sub_child.strip()))
        
        return hierarchical_relations

    def get_graph_statistics(self) -> Dict[str, any]:
        """获取知识图谱统计信息"""
        stats = {
            'total_nodes': len(self.nodes),
            'entity_types': defaultdict(int),
            'relationship_types': defaultdict(int),
            'concept_count': 0,
            'tech_term_count': 0,
            'relationship_count': 0
        }
        
        # 统计实体类型
        for node in self.nodes.values():
            stats['entity_types'][node.entity_type] += 1
            if node.entity_type == 'CONCEPT':
                stats['concept_count'] += 1
            elif node.entity_type == 'TECH_TERM':
                stats['tech_term_count'] += 1
        
        # 统计关系类型
        for node in self.nodes.values():
            for rel_type, targets in node.relationships.items():
                stats['relationship_types'][rel_type] += len(targets)
                stats['relationship_count'] += len(targets)
        
        return stats

    def add_node(self, id: str, content: str, source_video: str, 
                timestamp: float, difficulty: float = 0.5) -> KnowledgeNode:
        """添加知识点节点"""
        # 实体识别
        entities = self.extract_entities(content)
        if not entities:
            return None
            
        # 关系抽取
        relationships = self.extract_relationships(content, entities)
        
        # 为每个实体创建节点
        nodes = []
        for entity_text, entity_type, _, _ in entities:
            node_id = f"{id}_{len(nodes)}"
            node = KnowledgeNode(node_id, entity_text, source_video, timestamp, entity_type, difficulty)
            node.vector = self.model.encode(entity_text)
            
            # 存储到图中
            self.nodes[node_id] = node
            self.graph.add_node(node_id)
            nodes.append(node)
            
            # 存储到Neo4j
            if self.neo4j_graph:
                neo4j_node = Node(entity_type,
                                id=node_id,
                                content=entity_text,
                                source_video=source_video,
                                timestamp=timestamp)
                self.neo4j_graph.create(neo4j_node)
        
        # 建立关系
        for source, rel_type, target in relationships:
            source_node = next((n for n in nodes if n.content == source), None)
            target_node = next((n for n in nodes if n.content == target), None)
            
            if source_node and target_node:
                source_node.relationships[rel_type].append(target_node.id)
                self.graph.add_edge(source_node.id, target_node.id, type=rel_type)
                
                # 存储到Neo4j
                if self.neo4j_graph:
                    source_neo4j = self.neo4j_graph.nodes.match(id=source_node.id).first()
                    target_neo4j = self.neo4j_graph.nodes.match(id=target_node.id).first()
                    if source_neo4j and target_neo4j:
                        rel = Relationship(source_neo4j, rel_type, target_neo4j)
                        self.neo4j_graph.create(rel)
        
        # 更新向量索引
        if len(self.node_embeddings) > 0:
            self.node_embeddings = np.vstack([self.node_embeddings] + [n.vector for n in nodes])
        else:
            self.node_embeddings = np.array([n.vector for n in nodes])
        self.node_ids.extend([n.id for n in nodes])
        
        # 更新FAISS索引
        if len(self.nodes) > 1:
            if self.index is None:
                self.index = faiss.IndexFlatL2(nodes[0].vector.shape[0])
            self.index = faiss.IndexFlatL2(nodes[0].vector.shape[0])
            self.index.add(self.node_embeddings)
        
        return nodes[0] if nodes else None

    def analyze_content_relationships(self):
        """分析内容之间的关系"""
        if len(self.nodes) < 2:
            return

        # 使用向量相似度分析知识点关系
        for node1_id, node1 in self.nodes.items():
            node1_vector = node1.vector.reshape(-1)  # 确保是1维数组
            for node2_id, node2 in self.nodes.items():
                if node1_id != node2_id:
                    node2_vector = node2.vector.reshape(-1)  # 确保是1维数组
                    # 计算相似度
                    similarity = float(np.dot(node1_vector, node2_vector)) / (
                        float(np.linalg.norm(node1_vector)) * float(np.linalg.norm(node2_vector))
                    )
                    
                    # 如果相似度高，且时间戳早，则可能是前置知识
                    if similarity > 0.6:
                        if node1.timestamp < node2.timestamp:
                            if node1_id not in node2.prerequisites:
                                node2.prerequisites.append(node1_id)
                        else:
                            if node2_id not in node1.prerequisites:
                                node1.prerequisites.append(node2_id)

class LearningPathPlanner:
    """学习路径规划器"""
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.model = knowledge_graph.model

    def evaluate_user_level(self, user_background: str) -> Dict[str, float]:
        """评估用户对各个知识点的理解程度"""
        knowledge_levels = {}
        
        # 将用户背景转换为向量
        user_vector = self.model.encode(user_background).reshape(-1)  # 确保是1维数组
        
        # 计算用户背景与每个知识点的相似度
        for node_id, node in self.knowledge_graph.nodes.items():
            if node.vector is None:
                node.vector = self.model.encode(node.content)
            node_vector = node.vector.reshape(-1)  # 确保是1维数组
            
            # 计算余弦相似度
            similarity = float(np.dot(user_vector, node_vector)) / (
                float(np.linalg.norm(user_vector)) * float(np.linalg.norm(node_vector))
            )
            
            # 将相似度转换为理解程度（0-1之间）
            knowledge_levels[node_id] = max(0.0, min(1.0, similarity))
        
        return knowledge_levels

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        vec1 = self.model.encode(text1).reshape(-1)  # 确保是1维数组
        vec2 = self.model.encode(text2).reshape(-1)  # 确保是1维数组
        return float(np.dot(vec1, vec2)) / (
            float(np.linalg.norm(vec1)) * float(np.linalg.norm(vec2))
        )

    def generate_learning_path(self, user_background: str, target_topics: List[str]) -> List[str]:
        """生成个性化学习路径"""
        if not self.knowledge_graph.nodes:
            return []

        # 首先分析知识点之间的关系
        self.knowledge_graph.analyze_content_relationships()

        # 评估用户知识水平
        knowledge_levels = self.evaluate_user_level(user_background)
        
        # 找到与目标主题相关的知识点
        target_nodes = []
        for topic in target_topics:
            topic_vector = self.model.encode(topic).reshape(-1)  # 确保是1维数组
            for node_id, node in self.knowledge_graph.nodes.items():
                if node.vector is None:
                    node.vector = self.model.encode(node.content)
                node_vector = node.vector.reshape(-1)  # 确保是1维数组
                
                # 计算相似度
                similarity = float(np.dot(topic_vector, node_vector)) / (
                    float(np.linalg.norm(topic_vector)) * float(np.linalg.norm(node_vector))
                )
                
                if similarity > 0.5:  # 相似度阈值
                    # 考虑用户已有知识水平
                    if knowledge_levels.get(node_id, 0) < 0.7:  # 如果用户对该知识点的掌握程度不高
                        target_nodes.append((node_id, similarity))
        
        # 按相似度排序
        target_nodes.sort(key=lambda x: x[1], reverse=True)
        
        # 生成学习路径
        path = []
        visited = set()
        
        for node_id, _ in target_nodes:
            if node_id not in visited:
                # 添加前置知识点
                current_node = self.knowledge_graph.nodes[node_id]
                if current_node.prerequisites:
                    # 按时间戳排序前置知识
                    prereqs = sorted(
                        [(prereq_id, self.knowledge_graph.nodes[prereq_id].timestamp)
                         for prereq_id in current_node.prerequisites
                         if prereq_id in self.knowledge_graph.nodes],
                        key=lambda x: x[1]
                    )
                    for prereq_id, _ in prereqs:
                        if prereq_id not in visited and knowledge_levels.get(prereq_id, 0) < 0.7:
                            path.append(prereq_id)
                            visited.add(prereq_id)
                
                # 添加当前知识点
                path.append(node_id)
                visited.add(node_id)
        
        return path

class LearningProgressTracker:
    """学习进度追踪器"""
    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        self.progress = {}
    
    def update_progress(self, node_id: str, score: float):
        """更新学习进度"""
        self.progress[node_id] = score
    
    def get_progress(self) -> Dict[str, float]:
        """获取学习进度"""
        return self.progress
    
    def get_next_topic(self) -> Optional[str]:
        """获取下一个建议学习的主题"""
        # 找到进度最低的知识点
        min_score = float('inf')
        next_topic = None
        
        for node_id in self.knowledge_graph.nodes:
            score = self.progress.get(node_id, 0.0)
            if score < min_score:
                min_score = score
                next_topic = node_id
        
        return next_topic

class LearningPathSystem:
    # 初始化学习路径系统
    def __init__(self):
        self.planning_keywords = [
            "规划", "学习路径", "如何学", "怎么学", "学习方法",
            "学习计划", "路线图", "教学计划", "课程规划"
        ]
        
    # 判断是否为学习规划请求
    def is_planning_request(self, text: str) -> bool:
        return any(keyword in text for keyword in self.planning_keywords)
    
    # 生成学习规划
    def generate_plan(self, request: str) -> str:
        # 生成三个不同的方案
        plans = self._generate_multiple_plans(request)
        
        # 优化并整合方案
        final_plan = self._optimize_plans(plans, request)
        
        return final_plan
    
    # 生成多个学习方案
    def _generate_multiple_plans(self, request: str) -> List[str]:
        # 这里应实现实际的LLM调用逻辑
        # 示例返回三个方案
        return [
            self._generate_single_plan(request, "快速入门方案"),
            self._generate_single_plan(request, "深入学习方案"),
            self._generate_single_plan(request, "实践导向方案")
        ]
    
    # 生成单个学习方案
    def _generate_single_plan(self, request: str, plan_type: str) -> str:
        # 实际实现需要调用LLM
        return f"""
{plan_type}：

1. 学习目标
   - 目标1
   - 目标2

2. 学习步骤
   - 步骤1
   - 步骤2

3. 时间安排
   - 阶段1：xx时间
   - 阶段2：xx时间

4. 学习资源
   - 资源1
   - 资源2
"""
    
    # 优化并整合多个方案
    def _optimize_plans(self, plans: List[str], original_request: str) -> str:
        # 这里应该再次调用LLM来优化方案
        # 示例实现
        return f"""# 优化后的学习规划方案

## 总体目标
根据您的学习需求"{original_request}"，为您制定如下最优学习方案：

## 分阶段学习计划

### 第一阶段：基础入门
1. 学习内容...
2. 预期目标...
3. 建议时间...

### 第二阶段：进阶提升
1. 学习内容...
2. 预期目标...
3. 建议时间...

### 第三阶段：实战运用
1. 项目实践...
2. 技能提升...
3. 建议时间...

## 学习建议
1. 建议1...
2. 建议2...

## 推荐资源
1. 资源1...
2. 资源2...
"""