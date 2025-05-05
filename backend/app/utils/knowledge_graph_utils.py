"""知识图谱工具类"""
import logging
import json
import re
import traceback
import requests
import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from openai import OpenAI
from flask import request

# 直接使用固定的API密钥（与semantic_utils.py保持一致）
OPENAI_API_KEY = "sk-178e130a121445659860893fdfae1e7d"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "qwen2.5:7b"  # 默认使用qwen2.5:7b模型

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    """知识图谱管理器"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="cjx20040328", similarity_service=None):
        """初始化知识图谱管理器
        
        Args:
            uri: Neo4j数据库URI
            user: Neo4j用户名
            password: Neo4j密码
            similarity_service: 相似度服务实例
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
        # 设置相似度服务
        from services.llm_similarity_service import llm_similarity_service
        self.similarity_service = similarity_service or llm_similarity_service
        
    def connect(self):
        """连接Neo4j数据库"""
        try:
            if self.driver is None:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            return True
        except Exception as e:
            logger.error(f"Neo4j连接失败: {str(e)}")
            return False
            
    def close(self):
        """关闭Neo4j连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def get_all_video_nodes(self) -> List[Dict[str, Any]]:
        """获取所有视频节点
        
        Returns:
            视频节点列表，每个节点包含 video_id, title, tags 等属性
        """
        try:
            if not self.connect():
                logger.error("无法连接到Neo4j数据库")
                return []
                
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (v:Video)
                    RETURN v.video_id as video_id, v.title as title, v.tags as tags
                    """
                )
                
                videos = []
                for record in result:
                    videos.append({
                        'video_id': record['video_id'],
                        'title': record['title'],
                        'tags': record['tags']
                    })
                
                return videos
                
        except Exception as e:
            logger.error(f"获取视频节点失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        finally:
            self.close()
            
    def combine_knowledge_graphs(self, source_video_id, target_video_id, similarity_threshold=0.7) -> Optional[str]:
        """
        合并两个视频的知识图谱
        
        Args:
            source_video_id: 源视频ID（整数或字符串）
            target_video_id: 目标视频ID（整数或字符串）
            similarity_threshold: 相似度阈值，默认为0.7
            
        Returns:
            combined_video_id: 合并后的视频ID
        """
        try:
            # 确保视频ID是字符串类型
            source_video_id_str = str(source_video_id)
            target_video_id_str = str(target_video_id)
            
            logging.info(f"尝试合并知识图谱: 源视频ID={source_video_id_str}, 目标视频ID={target_video_id_str}")
            
            # 确保连接到数据库
            if not self.connect():
                logging.error("无法连接到Neo4j数据库")
                return None
                
            # 获取视频信息
            source_video = self.get_video_info(source_video_id_str)
            target_video = self.get_video_info(target_video_id_str)
            
            if not source_video or not target_video:
                logging.error(f"无法找到视频信息: source_id={source_video_id_str}, target_id={target_video_id_str}")
                return None
            
            source_title = source_video.get('title', f'视频{source_video_id_str}')
            target_title = target_video.get('title', f'视频{target_video_id_str}')
            
            # 获取合并前的知识点信息
            with self.driver.session() as session:
                # 获取源视频的知识点
                source_concepts = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.name AS name, c.description AS description
                    """,
                    video_id=source_video_id_str
                ).data()
                
                # 获取目标视频的知识点
                target_concepts = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.name AS name, c.description AS description
                    """,
                    video_id=target_video_id_str
                ).data()
                
                # 输出合并前的知识点信息
                logging.info(f"====== 合并知识图谱详细信息 ======")
                logging.info(f"源视频: {source_title} (ID: {source_video_id_str})")
                logging.info(f"源视频知识点数量: {len(source_concepts)}")
                for i, concept in enumerate(source_concepts):
                    logging.info(f"  {i+1}. {concept['name']}: {concept.get('description', '无描述')}")
                
                logging.info(f"目标视频: {target_title} (ID: {target_video_id_str})")
                logging.info(f"目标视频知识点数量: {len(target_concepts)}")
                for i, concept in enumerate(target_concepts):
                    logging.info(f"  {i+1}. {concept['name']}: {concept.get('description', '无描述')}")
            
            # 生成合并后的视频ID和标题
            combined_video_id = f"{source_video_id_str}_{target_video_id_str}"
            combined_title = f"{source_title} + {target_title}"
            
            # 合并标签
            source_tags = json.loads(source_video.get('tags', '[]'))
            target_tags = json.loads(target_video.get('tags', '[]'))
            combined_tags = list(set(source_tags + target_tags))
            
            # 使用Neo4j会话
            with self.driver.session() as session:
                # 1. 检查合并节点是否已存在，如果存在则删除
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    DETACH DELETE v
                    """,
                    video_id=combined_video_id
                )
                
                # 2. 创建合并节点
                session.run(
                    """
                    CREATE (v:Video {video_id: $video_id, title: $title, tags: $tags, is_combined: true})
                    """,
                    video_id=combined_video_id,
                    title=combined_title,
                    tags=json.dumps(combined_tags, ensure_ascii=False)
                )
                
                # 3. 复制源视频的所有概念到整合节点，并添加来源信息
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})-[:CONTAINS]->(concept:Concept)
                    MATCH (target:Video {video_id: $target_id})
                    CREATE (new_concept:Concept)
                    SET new_concept = concept
                    SET new_concept.source_video_id = $source_id
                    SET new_concept.source_video_title = $source_title
                    MERGE (target)-[:CONTAINS]->(new_concept)
                    WITH new_concept, concept
                    MATCH (concept)-[r:RELATED_TO]->(related:Concept)
                    MERGE (new_concept)-[:RELATED_TO]->(related)
                    """,
                    source_id=source_video_id_str,
                    target_id=combined_video_id,
                    source_title=source_title
                )
                
                # 4. 复制目标视频的所有概念到整合节点，并添加来源信息
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})-[:CONTAINS]->(concept:Concept)
                    MATCH (target:Video {video_id: $target_id})
                    CREATE (new_concept:Concept)
                    SET new_concept = concept
                    SET new_concept.source_video_id = $source_id
                    SET new_concept.source_video_title = $source_title
                    MERGE (target)-[:CONTAINS]->(new_concept)
                    WITH new_concept, concept
                    MATCH (concept)-[r:RELATED_TO]->(related:Concept)
                    MERGE (new_concept)-[:RELATED_TO]->(related)
                    """,
                    source_id=target_video_id_str,
                    target_id=combined_video_id,
                    source_title=target_title
                )
                
                # 5. 创建源视频和目标视频与整合节点的关系
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})
                    MATCH (target:Video {video_id: $target_id})
                    MATCH (combined:Video {video_id: $combined_id})
                    MERGE (source)-[:COMBINED_WITH]->(combined)
                    MERGE (target)-[:COMBINED_WITH]->(combined)
                    """,
                    source_id=source_video_id_str,
                    target_id=target_video_id_str,
                    combined_id=combined_video_id
                )
                
                # 6. 查找相似概念并创建关系
                # 获取源视频和目标视频的所有概念
                source_concepts = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.id AS id, c.label AS label, c.name AS name
                    """,
                    video_id=source_video_id_str
                ).data()
                
                target_concepts = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.id AS id, c.label AS label, c.name AS name
                    """,
                    video_id=target_video_id_str
                ).data()
                
                # 计算概念间的相似度并创建关系
                similar_pairs = []
                for source_concept in source_concepts:
                    for target_concept in target_concepts:
                        # 获取概念名称，优先使用name属性，如果没有则使用label属性
                        source_name = source_concept.get('name') or source_concept.get('label')
                        target_name = target_concept.get('name') or target_concept.get('label')
                        
                        if not source_name or not target_name:
                            continue
                            
                        # 计算概念标签的相似度
                        similarity = self.similarity_service.calculate_tag_similarity_with_llm(
                            source_name,
                            target_name
                        )
                        
                        # 如果相似度超过阈值，创建关系
                        if similarity >= similarity_threshold:
                            similar_pairs.append({
                                'source': source_name,
                                'target': target_name,
                                'similarity': similarity
                            })
                            
                            # 在合并节点中查找对应的概念
                            source_in_combined = session.run(
                                """
                                MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                                WHERE c.source_video_id = $source_id AND (c.name = $name OR c.label = $name)
                                RETURN c.id AS id
                                """,
                                video_id=combined_video_id,
                                source_id=source_video_id_str,
                                name=source_name
                            ).single()
                            
                            target_in_combined = session.run(
                                """
                                MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                                WHERE c.source_video_id = $source_id AND (c.name = $name OR c.label = $name)
                                RETURN c.id AS id
                                """,
                                video_id=combined_video_id,
                                source_id=target_video_id_str,
                                name=target_name
                            ).single()
                            
                            # 如果找到了对应的概念，创建关系
                            if source_in_combined and target_in_combined:
                                session.run(
                                    """
                                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(source:Concept)
                                    WHERE source.id = $source_id
                                    MATCH (v)-[:CONTAINS]->(target:Concept)
                                    WHERE target.id = $target_id
                                    MERGE (source)-[r:SIMILAR_TO {similarity: $similarity}]->(target)
                                    """,
                                    video_id=combined_video_id,
                                    source_id=source_in_combined['id'],
                                    target_id=target_in_combined['id'],
                                    similarity=similarity
                                )
                
                # 获取合并后的知识点信息
                combined_concepts = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.name AS name, c.label AS label, c.description AS description, 
                           c.source_video_id AS source_id, c.source_video_title AS source_title
                    """,
                    video_id=combined_video_id
                ).data()
                
                # 输出合并后的知识点信息
                logging.info(f"合并后的视频: {combined_title} (ID: {combined_video_id})")
                logging.info(f"合并后的知识点数量: {len(combined_concepts)}")
                
                # 按来源分组显示知识点
                source_concepts_after = [c for c in combined_concepts if str(c.get('source_id')) == source_video_id_str]
                target_concepts_after = [c for c in combined_concepts if str(c.get('source_id')) == target_video_id_str]
                
                logging.info(f"来自源视频的知识点数量: {len(source_concepts_after)}")
                for i, concept in enumerate(source_concepts_after):
                    name = concept.get('name') or concept.get('label', '未命名')
                    logging.info(f"  {i+1}. {name}: {concept.get('description', '无描述')}")
                
                logging.info(f"来自目标视频的知识点数量: {len(target_concepts_after)}")
                for i, concept in enumerate(target_concepts_after):
                    name = concept.get('name') or concept.get('label', '未命名')
                    logging.info(f"  {i+1}. {name}: {concept.get('description', '无描述')}")
                
                logging.info(f"相似知识点对数量: {len(similar_pairs)}")
                for i, pair in enumerate(similar_pairs):
                    logging.info(f"  {i+1}. {pair['source']} <-> {pair['target']} (相似度: {pair['similarity']:.2f})")
                
                logging.info(f"====== 合并知识图谱完成 ======")
                
                return combined_video_id
                
        except Exception as e:
            logging.error(f"整合知识图谱失败: {e}")
            logging.error(traceback.format_exc())
            return None
            
    def combine_multiple_knowledge_graphs(self, video_ids: List[int], similarity_threshold=0.7) -> Optional[str]:
        """
        合并多个视频的知识图谱
        
        Args:
            video_ids: 要合并的视频ID列表
            similarity_threshold: 相似度阈值，默认为0.7
            
        Returns:
            combined_video_id: 合并后的视频ID
        """
        if not video_ids or len(video_ids) < 2:
            logging.error("至少需要两个视频才能进行合并")
            return None
            
        try:
            # 确保连接到数据库
            if not self.connect():
                logging.error("无法连接到Neo4j数据库")
                return None
                
            # 获取所有视频信息
            videos_info = []
            for video_id in video_ids:
                video_info = self.get_video_info(video_id)
                if not video_info:
                    logging.error(f"无法找到视频信息: video_id={video_id}")
                    return None
                videos_info.append(video_info)
            
            # 生成合并后的视频ID和标题
            combined_video_id = "combined_" + "_".join([str(vid) for vid in video_ids])
            combined_title = " + ".join([info.get('title', f'视频{info.get("video_id")}') for info in videos_info])
            
            # 合并所有标签
            all_tags = []
            for video_info in videos_info:
                try:
                    tags = json.loads(video_info.get('tags', '[]'))
                    all_tags.extend(tags)
                except json.JSONDecodeError:
                    logging.warning(f"视频 {video_info.get('video_id')} 的标签格式无效")
            
            # 去重
            combined_tags = list(set(all_tags))
            
            # 使用Neo4j会话
            with self.driver.session() as session:
                # 1. 检查合并节点是否已存在，如果存在则删除
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    DETACH DELETE v
                    """,
                    video_id=combined_video_id
                )
                
                # 2. 创建合并节点
                session.run(
                    """
                    CREATE (v:Video {video_id: $video_id, title: $title, tags: $tags, is_combined: true})
                    """,
                    video_id=combined_video_id,
                    title=combined_title,
                    tags=json.dumps(combined_tags, ensure_ascii=False)
                )
                
                # 3. 复制每个视频的所有概念到合并节点，并添加来源信息
                for video_info in videos_info:
                    video_id = video_info.get('video_id')
                    video_title = video_info.get('title', f'视频{video_id}')
                    
                    session.run(
                        """
                        MATCH (source:Video {video_id: $source_id})-[:CONTAINS]->(concept:Concept)
                        MATCH (target:Video {video_id: $target_id})
                        CREATE (new_concept:Concept)
                        SET new_concept = concept
                        SET new_concept.source_video_id = $source_id
                        SET new_concept.source_video_title = $source_title
                        MERGE (target)-[:CONTAINS]->(new_concept)
                        WITH new_concept, concept
                        MATCH (concept)-[r:RELATED_TO]->(related:Concept)
                        MERGE (new_concept)-[:RELATED_TO]->(related)
                        """,
                        source_id=video_id,
                        target_id=combined_video_id,
                        source_title=video_title
                    )
                    
                    # 4. 创建源视频与合并节点的关系
                    session.run(
                        """
                        MATCH (source:Video {video_id: $source_id})
                        MATCH (combined:Video {video_id: $combined_id})
                        MERGE (source)-[:COMBINED_WITH]->(combined)
                        """,
                        source_id=video_id,
                        combined_id=combined_video_id
                    )
                
                # 5. 获取所有视频的概念
                all_concepts = []
                for video_info in videos_info:
                    video_id = video_info.get('video_id')
                    concepts = session.run(
                        """
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                        RETURN c.id AS id, c.label AS label, c.name AS name
                        """,
                        video_id=video_id
                    ).data()
                    all_concepts.extend(concepts)
                
                # 6. 计算不同视频的概念之间的相似度并创建关系
                for i, concept1 in enumerate(all_concepts):
                    for concept2 in all_concepts[i+1:]:
                        # 只比较不同视频的概念
                        if concept1['video_id'] == concept2['video_id']:
                            continue
                            
                        # 获取概念名称，优先使用name属性，如果没有则使用label属性
                        source_name = concept1.get('name') or concept1.get('label')
                        target_name = concept2.get('name') or concept2.get('label')
                        
                        if not source_name or not target_name:
                            continue
                            
                        # 计算概念标签的相似度
                        similarity = self.similarity_service.calculate_tag_similarity_with_llm(
                            source_name,
                            target_name
                        )
                        
                        # 如果相似度超过阈值，创建关系
                        if similarity >= similarity_threshold:
                            # 在合并节点中查找对应的概念
                            source_in_combined = session.run(
                                """
                                MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                                WHERE c.source_video_id = $source_id AND (c.name = $name OR c.label = $name)
                                RETURN c.id AS id
                                """,
                                video_id=combined_video_id,
                                source_id=concept1['video_id'],
                                name=source_name
                            ).single()
                            
                            target_in_combined = session.run(
                                """
                                MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                                WHERE c.source_video_id = $source_id AND (c.name = $name OR c.label = $name)
                                RETURN c.id AS id
                                """,
                                video_id=combined_video_id,
                                source_id=concept2['video_id'],
                                name=target_name
                            ).single()
                            
                            # 如果找到了对应的概念，创建关系
                            if source_in_combined and target_in_combined:
                                session.run(
                                    """
                                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(source:Concept)
                                    WHERE source.id = $source_id
                                    MATCH (v)-[:CONTAINS]->(target:Concept)
                                    WHERE target.id = $target_id
                                    MERGE (source)-[r:SIMILAR_TO {similarity: $similarity}]->(target)
                                    """,
                                    video_id=combined_video_id,
                                    source_id=source_in_combined['id'],
                                    target_id=target_in_combined['id'],
                                    similarity=similarity
                                )
                
                return combined_video_id
                
        except Exception as e:
            logging.error(f"整合多个知识图谱失败: {e}")
            logging.error(traceback.format_exc())
            return None
            
    def get_video_info(self, video_id):
        """
        获取视频信息
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频信息字典
        """
        try:
            # 确保视频ID是字符串类型
            video_id_str = str(video_id)
            logging.info(f"获取视频信息: video_id={video_id_str}")
            
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.video_id as video_id, v.title as title, v.tags as tags
                    """,
                    video_id=video_id_str
                ).single()
                
                if result:
                    logging.info(f"成功获取视频信息: {result['title']}")
                    return {
                        'video_id': result['video_id'],
                        'title': result['title'],
                        'tags': result['tags']
                    }
                
                logging.error(f"未找到视频信息: video_id={video_id_str}")
                return None
                
        except Exception as e:
            logging.error(f"获取视频信息失败: {e}")
            return None
            
    def get_knowledge_graph(self, video_id) -> Dict[str, Any]:
        """获取视频的知识图谱
        
        Args:
            video_id: 视频ID，可以是整数或字符串（如"1_2"表示合并视频）
            
        Returns:
            包含节点和连接的知识图谱数据
        """
        try:
            # 确保 video_id 是字符串类型
            video_id = str(video_id)
            
            # 检查是否是合并视频ID（包含下划线）
            is_combined_video = "_" in video_id
            
            logging.info(f"获取视频 {video_id} 的知识图谱，是否是合并视频: {is_combined_video}")
            
            if not self.connect():
                raise Exception("无法连接到Neo4j数据库")
                
            with self.driver.session() as session:
                # 检查是否为合并视频
                # 1. 检查视频本身是否是合并视频
                is_combined = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.is_combined as is_combined
                    """,
                    video_id=video_id
                ).single()
                
                # 2. 检查视频是否参与了合并
                is_part_of_combined = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:COMBINED_WITH]->(combined:Video)
                    RETURN combined.video_id as combined_id
                    """,
                    video_id=video_id
                ).single()
                
                # 如果视频本身是合并视频，或者参与了合并，则使用合并视频ID
                is_combined_video = (is_combined and is_combined["is_combined"]) or is_part_of_combined
                
                # 如果视频参与了合并，使用合并视频ID
                if is_part_of_combined:
                    combined_id = is_part_of_combined["combined_id"]
                    logging.info(f"视频 {video_id} 参与了合并，合并视频ID为 {combined_id}")
                    video_id = combined_id
                    
                # 查询与视频相关的知识点
                if is_combined_video:
                    logging.info(f"获取合并视频 {video_id} 的知识图谱")
                    
                    # 首先获取所有概念节点
                    concepts_query = """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c
                    """
                    
                    concepts_result = session.run(concepts_query, video_id=video_id)
                    concepts = list(concepts_result)
                    
                    # 获取原始视频节点
                    source_videos_query = """
                    MATCH (v:Video {video_id: $video_id})<-[:COMBINED_WITH]-(source:Video)
                    RETURN source.video_id as video_id, source.title as title
                    """
                    
                    source_videos_result = session.run(source_videos_query, video_id=video_id)
                    source_videos = list(source_videos_result)
                    logging.info(f"找到 {len(source_videos)} 个原始视频")
                    
                    # 再获取所有关系
                    logging.info(f"查询合并视频 {video_id} 的所有关系")
                    
                    # 查询相似关系
                    similar_relations = []
                    
                    # 获取原始视频的知识点关系结构
                    source_concepts_map = {}
                    
                    # 对每个原始视频，获取其一级和二级知识点
                    for source_video in source_videos:
                        source_id = source_video['video_id']
                        source_title = source_video['title']
                        logging.info(f"获取原始视频 {source_id} ({source_title}) 的知识点层次结构")
                        
                        # 查询原始视频的知识点层次结构
                        hierarchy_query = """
                        MATCH (v:Video {video_id: $source_id})-[:CONTAINS]->(c:Concept)
                        OPTIONAL MATCH (c)-[:RELATED_TO]->(related:Concept)
                        RETURN c.name as name, c.label as label, collect(related.name) as related_concepts
                        """
                        
                        hierarchy_result = session.run(hierarchy_query, source_id=source_id)
                        hierarchy_data = list(hierarchy_result)
                        
                        # 分析知识点层次结构
                        # 对于合并视频，我们将原始视频的知识点分为一级知识点和二级知识点
                        primary_concepts = []
                        secondary_concepts = []
                        concept_relations = {}
                        
                        for item in hierarchy_data:
                            concept_name = item['name'] or item['label']
                            related_concepts = item['related_concepts']
                            
                            if concept_name:
                                # 将知识点添加为一级知识点
                                primary_concepts.append(concept_name)
                                
                                # 存储该知识点的相关知识点（二级知识点）
                                if related_concepts:
                                    concept_relations[concept_name] = related_concepts
                                    # 将相关知识点添加为二级知识点
                                    for related in related_concepts:
                                        if related not in primary_concepts and related not in secondary_concepts:
                                            secondary_concepts.append(related)
                        
                        # 存储原始视频的知识点层次结构
                        source_concepts_map[source_id] = {
                            'title': source_title,
                            'primary': primary_concepts,
                            'secondary': secondary_concepts,
                            'concept_relations': concept_relations  # 存储一级知识点和二级知识点的关系
                        }
                        
                        logging.info(f"原始视频 {source_id} 有 {len(primary_concepts)} 个一级知识点和 {len(secondary_concepts)} 个二级知识点")
                    
                    # 查询跨视频的相似关系，只保留相似度高的关系
                    logging.info(f"查询跨视频的高相似度知识点关系")
                    
                    similar_query = """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c1:Concept)
                    MATCH (v)-[:CONTAINS]->(c2:Concept)
                    WHERE c1 <> c2 AND c1.source_video_id <> c2.source_video_id
                    MATCH (c1)-[r:SIMILAR_TO]->(c2)
                    WHERE r.similarity >= 0.8  // 只保留相似度较高的关系
                    RETURN 
                        CASE WHEN c1.name IS NOT NULL THEN c1.name ELSE c1.label END as source, 
                        CASE WHEN c2.name IS NOT NULL THEN c2.name ELSE c2.label END as target, 
                        'SIMILAR_TO' as relationship, 
                        r.similarity as similarity
                    """
                    
                    similar_result = session.run(similar_query, video_id=video_id)
                    similar_relations = list(similar_result)
                    logging.info(f"找到 {len(similar_relations)} 个高相似度关系")
                    
                    # 如果还是没有找到相似关系，尝试使用最简单的查询
                    if len(similar_relations) == 0:
                        logging.info(f"尝试使用最简单的查询获取相似关系")
                        simple_similar_query = """
                        MATCH (c1)-[r:SIMILAR_TO]->(c2)
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c1)
                        MATCH (v)-[:CONTAINS]->(c2)
                        RETURN 
                            CASE WHEN c1.name IS NOT NULL THEN c1.name ELSE c1.label END as source, 
                            CASE WHEN c2.name IS NOT NULL THEN c2.name ELSE c2.label END as target, 
                            'SIMILAR_TO' as relationship, 
                            r.similarity as similarity
                        """
                        simple_result = session.run(simple_similar_query, video_id=video_id)
                        simple_similar_relations = list(simple_result)
                        logging.info(f"简单查询找到 {len(simple_similar_relations)} 个相似关系")
                        similar_relations.extend(simple_similar_relations)
                    
                    # 查询普通关系
                    related_relations = []
                    
                    # 查询原始视频内部的知识点关系
                    related_relations = []
                    
                    # 对每个原始视频，获取其内部知识点关系
                    for source_video in source_videos:
                        source_id = source_video['video_id']
                        logging.info(f"查询原始视频 {source_id} 的内部知识点关系")
                        
                        # 查询原始视频内部的知识点关系
                        source_relations_query = """
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c1:Concept)
                        MATCH (v)-[:CONTAINS]->(c2:Concept)
                        WHERE c1 <> c2 AND c1.source_video_id = $source_id AND c2.source_video_id = $source_id
                        MATCH (c1)-[r:RELATED_TO]->(c2)
                        RETURN 
                            CASE WHEN c1.name IS NOT NULL THEN c1.name ELSE c1.label END as source, 
                            CASE WHEN c2.name IS NOT NULL THEN c2.name ELSE c2.label END as target, 
                            'RELATED_TO' as relationship, 
                            null as similarity
                        """
                        
                        source_result = session.run(source_relations_query, video_id=video_id, source_id=source_id)
                        source_related = list(source_result)
                        logging.info(f"找到 {len(source_related)} 个原始视频 {source_id} 的内部关系")
                        related_relations.extend(source_related)
                    
                    # 如果没有找到普通关系，尝试使用最简单的查询
                    if len(related_relations) == 0:
                        logging.info(f"尝试使用最简单的查询获取普通关系")
                        simple_related_query = """
                        MATCH (c1)-[r:RELATED_TO]->(c2)
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c1)
                        MATCH (v)-[:CONTAINS]->(c2)
                        RETURN 
                            CASE WHEN c1.name IS NOT NULL THEN c1.name ELSE c1.label END as source, 
                            CASE WHEN c2.name IS NOT NULL THEN c2.name ELSE c2.label END as target, 
                            'RELATED_TO' as relationship, 
                            null as similarity
                        """
                        simple_result = session.run(simple_related_query, video_id=video_id)
                        simple_related_relations = list(simple_result)
                        logging.info(f"简单查询找到 {len(simple_related_relations)} 个普通关系")
                        related_relations.extend(simple_related_relations)
                    
                    # 合并两种关系
                    relations = similar_relations + related_relations
                    logging.info(f"总共找到 {len(relations)} 个关系，其中相似关系 {len(similar_relations)} 个，普通关系 {len(related_relations)} 个")
                    
                    # 构建节点和连接
                    nodes = []
                    links = []
                    node_ids = set()
                    
                    # 添加视频主节点
                    video_info = session.run(
                        """
                        MATCH (v:Video {video_id: $video_id})
                        RETURN v.title as title
                        """,
                        video_id=video_id
                    ).single()
                    
                    if video_info:
                        # 创建主视频节点
                        video_node = {
                            "id": f"video-{video_id}",
                            "name": video_info["title"],
                            "label": video_info["title"],
                            "main": True,
                            "type": "video",
                            "videoId": video_id,
                            "itemStyle": {"color": "#F472B6"},  # 粉色，与图例说明一致
                            "symbolSize": 60,
                            "expanded": True,
                            "isMainNode": True
                        }
                        nodes.append(video_node)
                        node_ids.add(f"video-{video_id}")
                    
                    # 在合并视频的情况下，我们需要区分当前选择的视频和其他视频
                    # 当前选择的视频的知识点显示为一级知识点，其他视频的知识点显示为“其他视频相似知识点”
                    # 获取当前选择的视频ID（合并视频ID的格式为“target_id_source_id”）
                    current_selected_video_id = None
                    if "_" in video_id:
                        parts = video_id.split("_")
                        if len(parts) == 2:
                            current_selected_video_id = parts[0]  # 当前选择的视频ID
                            logging.info(f"当前选择的视频ID: {current_selected_video_id}")
                    
                    # 创建一个字典，存储每个原始视频的标题
                    source_video_titles = {}
                    for source_video in source_videos:
                        source_video_titles[source_video['video_id']] = source_video['title']
                    
                    logging.info(f"合并视频包含的原始视频: {source_video_titles}")
                    
                    # 记录所有已添加的知识点
                    all_added_concepts = set()
                    
                    # 遍历所有原始视频，处理其知识点
                    for source_video in source_videos:
                        source_id = source_video['video_id']
                        source_title = source_video['title']
                        
                        if source_id not in source_concepts_map:
                            logging.info(f"原始视频 {source_id} 没有知识点数据，跳过")
                            continue
                        
                        # 获取原始视频的知识点数据
                        video_data = source_concepts_map[source_id]
                        logging.info(f"处理原始视频 {source_id} ({source_title}) 的知识点")
                        
                        # 检查原始视频是否有一级知识点
                        has_primary_concepts = len(video_data['primary']) > 0
                        logging.info(f"原始视频 {source_id} 是否有一级知识点: {has_primary_concepts}")
                        
                        # 1. 先添加原始视频的一级知识点（蓝色）
                        for concept_name in video_data['primary']:
                            # 如果该知识点已经添加，则跳过
                            if concept_name in all_added_concepts:
                                logging.info(f"知识点 '{concept_name}' 已经添加，跳过")
                                continue
                                
                            concept_id = f"concept-{concept_name}"
                            
                            if concept_id not in node_ids:
                                # 判断该知识点是否来自当前选择的视频
                                is_from_current_selected_video = str(source_id) == str(current_selected_video_id)
                                
                                # 如果来自当前选择的视频，显示为一级知识点（蓝色）
                                # 如果来自其他视频，显示为“其他视频相似知识点”（黄色）
                                node_type = "primary_concept" if is_from_current_selected_video else "similar_concept"
                                node_color = "#5470c6" if is_from_current_selected_video else "#fac858"  # 蓝色或黄色
                                
                                node_data = {
                                    "id": concept_id,
                                    "name": concept_name,
                                    "label": concept_name,
                                    "description": "",
                                    "main": is_from_current_selected_video,  # 只有当前选择的视频的知识点才是主要的
                                    "expanded": True,
                                    "videoId": video_id,
                                    "type": node_type,
                                    "symbolSize": 40 if is_from_current_selected_video else 35,  # 当前视频的知识点稍大一点
                                    "isPrimaryKnowledge": is_from_current_selected_video,
                                    "isFromCurrentVideo": is_from_current_selected_video,
                                    "itemStyle": {"color": node_color},
                                    "source_video_id": source_id,
                                    "source_video_title": source_title
                                }
                                
                                nodes.append(node_data)
                                node_ids.add(concept_id)
                                all_added_concepts.add(concept_name)
                                
                                # 将视频节点与一级知识点相连
                                links.append({
                                    "source": f"video-{video_id}",
                                    "target": concept_id,
                                    "relationship": "PRIMARY",
                                    "lineStyle": {"width": 3, "color": "#5470c6"}
                                })
                        
                        # 2. 然后添加原始视频的二级知识点
                        # 如果原始视频没有一级知识点，则将二级知识点显示为蓝色，否则显示为绿色
                        secondary_color = "#5470c6" if not has_primary_concepts else "#91cc75"  # 没有一级知识点时使用蓝色，否则使用绿色
                        secondary_size = 40 if not has_primary_concepts else 30  # 没有一级知识点时使用更大的尺寸
                        
                        for concept_name in video_data['secondary']:
                            # 跳过已经作为一级知识点的概念
                            if concept_name in video_data['primary']:
                                continue
                                
                            # 如果该知识点已经添加，则跳过
                            if concept_name in all_added_concepts:
                                logging.info(f"知识点 '{concept_name}' 已经添加，跳过")
                                continue
                                
                            concept_id = f"concept-{concept_name}"
                            
                            if concept_id not in node_ids:
                                node_data = {
                                    "id": concept_id,
                                    "name": concept_name,
                                    "label": concept_name,
                                    "description": "",
                                    "main": not has_primary_concepts,  # 如果没有一级知识点，则将二级知识点标记为主要
                                    "expanded": True,
                                    "videoId": video_id,
                                    "type": "secondary_concept",
                                    "symbolSize": secondary_size,
                                    "isPrimaryKnowledge": not has_primary_concepts,  # 如果没有一级知识点，则将二级知识点视为一级
                                    "isSecondaryKnowledge": has_primary_concepts,  # 如果有一级知识点，则保持二级知识点的属性
                                    "isFromCurrentVideo": True,  # 对于合并视频，所有原始视频都视为当前视频
                                    "itemStyle": {"color": secondary_color},
                                    "source_video_id": source_id,
                                    "source_video_title": source_title
                                }
                                
                                nodes.append(node_data)
                                node_ids.add(concept_id)
                                # 判断该知识点是否来自当前选择的视频
                                is_from_current_selected_video = str(source_id) == str(current_selected_video_id)
                                
                                # 当前选择的视频的知识点与视频节点相连使用蓝色实线
                                # 其他视频的知识点与视频节点相连使用红色虚线
                                if not has_primary_concepts:
                                    if is_from_current_selected_video:
                                        # 当前选择的视频的知识点使用蓝色实线
                                        links.append({
                                            "source": f"video-{video_id}",
                                            "target": concept_id,
                                            "relationship": "PRIMARY",
                                            "lineStyle": {"width": 3, "color": "#3B82F6"}  # 蓝色
                                        })
                                    else:
                                        # 其他视频的知识点使用红色虚线
                                        # 注意：前端会根据 relationship 类型来设置虚线样式，而不是使用 lineStyle.type
                                        links.append({
                                            "source": f"video-{video_id}",
                                            "target": concept_id,
                                            "relationship": "SIMILAR_TO",  # 这里必须设置为 SIMILAR_TO，前端才会显示为虚线
                                            "lineStyle": {"width": 2, "color": "#FF6B6B"}  # 红色
                                        })
                                # 二级知识点和其他视频的知识点不与视频节点相连
                    
                    # 我们已经在上面处理了所有原始视频的知识点
                    # 不再需要单独处理相似视频的知识点
                    
                    # 处理所有视频的二级知识点与一级知识点的关系
                    # 创建一个字典，记录每个知识点来自哪个视频
                    concept_source_map = {}
                    
                    # 处理当前选择的视频的二级知识点与一级知识点的关系
                    if current_selected_video_id and current_selected_video_id in source_concepts_map:
                        video_data = source_concepts_map[current_selected_video_id]
                        concept_relations = video_data.get('concept_relations', {})
                        
                        # 记录当前选择视频的所有知识点
                        for concept in video_data['primary'] + video_data['secondary']:
                            concept_source_map[concept] = current_selected_video_id
                        
                        # 首先添加当前选择视频的所有二级知识点节点
                        for secondary_concept in video_data['secondary']:
                            # 检查该二级知识点是否已经添加
                            concept_id = f"concept-{secondary_concept}"
                            if concept_id not in node_ids:
                                # 添加当前选择视频的二级知识点节点
                                nodes.append({
                                    "id": concept_id,
                                    "name": secondary_concept,
                                    "symbolSize": 40,
                                    "category": "secondary_concept",  # 二级知识点类别
                                    "itemStyle": {"color": "#10B981"}  # 绿色，与前端一致
                                })
                                node_ids.add(concept_id)
                                all_added_concepts.add(secondary_concept)
                        
                        # 然后添加当前选择视频的一级知识点和二级知识点之间的关系
                        for primary_concept, related_concepts in concept_relations.items():
                            for secondary_concept in related_concepts:
                                # 跳过一级知识点
                                if secondary_concept == primary_concept:
                                    continue
                                
                                # 确保二级知识点已经添加到节点中
                                if f"concept-{secondary_concept}" not in node_ids:
                                    continue
                                        
                                # 添加二级知识点与一级知识点的关系
                                links.append({
                                    "source": f"concept-{primary_concept}",
                                    "target": f"concept-{secondary_concept}",
                                    "relationship": "RELATED_TO",
                                    "lineStyle": {"width": 1.5, "color": "#73c0de"}  # 浅蓝色
                                })
                                logging.info(f"添加当前选择视频的二级知识点与一级知识点的关系: {primary_concept} -> {secondary_concept}")
                    
                    # 处理其他视频的二级知识点
                    for source_id, video_data in source_concepts_map.items():
                        # 跳过当前选择的视频，因为已经处理过了
                        if current_selected_video_id and str(source_id) == str(current_selected_video_id):
                            continue
                            
                        concept_relations = video_data.get('concept_relations', {})
                        
                        # 记录其他视频的所有知识点
                        for concept in video_data['primary'] + video_data['secondary']:
                            # 如果该知识点还没有被记录来源，或者不是当前选择的视频的知识点
                            if concept not in concept_source_map:
                                concept_source_map[concept] = source_id
                        
                        # 首先添加其他视频的所有一级知识点节点
                        for primary_concept in video_data['primary']:
                            # 检查该一级知识点是否已经添加
                            concept_id = f"concept-{primary_concept}"
                            
                            # 如果该知识点尚未添加，则添加为其他视频的一级知识点
                            if concept_id not in node_ids and primary_concept not in all_added_concepts:
                                # 添加其他视频的一级知识点节点，使用黄色
                                nodes.append({
                                    "id": concept_id,
                                    "name": primary_concept,
                                    "symbolSize": 50,
                                    "category": "similar_concept",  # 其他视频的一级知识点类别
                                    "itemStyle": {"color": "#EAB308"}  # 黄色，与前端图例一致
                                })
                                node_ids.add(concept_id)
                                all_added_concepts.add(primary_concept)
                                logging.info(f"添加其他视频的一级知识点: {primary_concept}")
                                
                                # 其他视频的一级知识点与当前视频节点之间的连线使用红色虚线
                                links.append({
                                    "source": f"video-{video_id}",
                                    "target": concept_id,
                                    "relationship": "SIMILAR_TO",  # 这里必须设置为 SIMILAR_TO，前端才会显示为虚线
                                    "lineStyle": {"width": 2, "color": "#FF6B6B"}  # 红色
                                })
                                logging.info(f"添加其他视频的一级知识点与视频节点的连线: video-{video_id} -> {primary_concept}")
                            # 如果该知识点已经添加，但是当前选择的视频的二级知识点，则更新其类别和颜色
                            elif concept_id in node_ids and primary_concept in all_added_concepts:
                                # 查找该节点并更新其类别和颜色
                                for node in nodes:
                                    if node["id"] == concept_id:
                                        # 如果该知识点不是当前选择的视频的知识点，则更新其类别和颜色
                                        if concept_source_map.get(primary_concept) != current_selected_video_id:
                                            node["category"] = "similar_concept"
                                            node["itemStyle"] = {"color": "#EAB308"}  # 黄色，与前端图例一致
                                            logging.info(f"更新知识点 {primary_concept} 的类别和颜色为其他视频的一级知识点")
                                        break
                        
                        # 首先添加其他视频的所有二级知识点节点
                        for secondary_concept in video_data['secondary']:
                            # 检查该二级知识点是否已经添加
                            concept_id = f"concept-{secondary_concept}"
                            
                            # 如果该知识点尚未添加，则添加为其他视频的二级知识点
                            if concept_id not in node_ids and secondary_concept not in all_added_concepts:
                                # 添加其他视频的二级知识点节点，使用更深的黄色
                                nodes.append({
                                    "id": concept_id,
                                    "name": secondary_concept,
                                    "symbolSize": 40,
                                    "category": "similar_secondary_concept",  # 其他视频的二级知识点类别
                                    "itemStyle": {"color": "#e6a23c"}  # 更深的黄色，与前端图例一致
                                })
                                node_ids.add(concept_id)
                                all_added_concepts.add(secondary_concept)
                                logging.info(f"添加其他视频的二级知识点: {secondary_concept}")
                            # 如果该知识点已经添加，但是当前选择的视频的二级知识点，则更新其类别和颜色
                            elif concept_id in node_ids and secondary_concept in all_added_concepts:
                                # 查找该节点并更新其类别和颜色
                                for node in nodes:
                                    if node["id"] == concept_id:
                                        # 如果该知识点不是当前选择的视频的知识点，则更新其类别和颜色
                                        if concept_source_map.get(secondary_concept) != current_selected_video_id:
                                            node["category"] = "similar_secondary_concept"
                                            node["itemStyle"] = {"color": "#e6a23c"}  # 更深的黄色
                                            logging.info(f"更新知识点 {secondary_concept} 的类别和颜色为其他视频的二级知识点")
                                        break
                        
                        # 然后添加其他视频的一级知识点和二级知识点之间的关系
                        for primary_concept, related_concepts in concept_relations.items():
                            # 确保一级知识点已经添加到节点中
                            primary_id = f"concept-{primary_concept}"
                            if primary_id not in node_ids:
                                continue
                                
                            for secondary_concept in related_concepts:
                                # 跳过一级知识点
                                if secondary_concept == primary_concept:
                                    continue
                                
                                # 确保二级知识点已经添加到节点中
                                secondary_id = f"concept-{secondary_concept}"
                                if secondary_id not in node_ids:
                                    continue
                                
                                # 确保这两个知识点之间的关系还没有添加
                                relation_exists = False
                                for link in links:
                                    if (link["source"] == primary_id and link["target"] == secondary_id) or \
                                       (link["source"] == secondary_id and link["target"] == primary_id):
                                        relation_exists = True
                                        break
                                
                                if relation_exists:
                                    continue
                                        
                                # 添加其他视频的二级知识点与一级知识点的关系
                                links.append({
                                    "source": primary_id,
                                    "target": secondary_id,
                                    "relationship": "RELATED_TO",
                                    "lineStyle": {"width": 1.5, "color": "#e6a23c"}  # 更深的黄色的连接线
                                })
                                logging.info(f"添加其他视频的二级知识点与一级知识点的关系: {primary_concept} -> {secondary_concept}")
                    
                    # 添加相似关系，只添加当前选择的视频的知识点与其他视频的知识点之间的相似关系
                    for relation in relations:
                        if not relation["source"] or not relation["target"] or not relation["relationship"]:
                            continue
                        
                        # 检查这两个知识点是否在我们的知识图谱中
                        source_id = f"concept-{relation['source']}"
                        target_id = f"concept-{relation['target']}"
                        
                        if source_id not in node_ids or target_id not in node_ids:
                            continue
                        
                        # 添加连接
                        link_data = {
                            "source": source_id,
                            "target": target_id,
                            "relationship": relation["relationship"]
                        }
                        
                        # 为不同类型的关系设置不同的样式
                        if relation["relationship"] == "SIMILAR_TO":
                            similarity = relation.get("similarity", 0.7)
                            link_data["similarity"] = float(similarity)
                            link_data["lineStyle"] = {
                                "width": 2, 
                                "color": "#ee6666",  # 红色
                                "type": "dashed"
                            }
                            logging.info(f"找到相似关系: {relation['source']} <-> {relation['target']} (相似度: {similarity})")
                        elif relation["relationship"] == "RELATED_TO":
                            link_data["lineStyle"] = {
                                "width": 1.5, 
                                "color": "#73c0de"  # 浅蓝色
                            }
                        
                        links.append(link_data)
                    
                    logging.info(f"合并视频知识图谱构建完成，节点数: {len(nodes)}，连接数: {len(links)}")
                    return {"nodes": nodes, "links": links}
                else:
                    # 对于普通视频，获取所有知识点并以视频节点为中心
                    # 修改查询，确保能够获取所有一级知识点和二级知识点
                    try:
                        # 首先获取视频信息和所有知识点
                        video_info_query = """
                        MATCH (v:Video {video_id: $video_id})
                        RETURN v.title as video_title, v.tags as tags
                        """
                        
                        video_info = session.run(video_info_query, video_id=video_id).single()
                        if not video_info:
                            logging.error(f"找不到视频 {video_id} 的信息")
                            return {"nodes": [], "links": []}
                            
                        video_title = video_info["video_title"]
                        tags = video_info.get("tags", [])
                        
                        # 获取所有知识点
                        concepts_query = """
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                        RETURN c.name as name
                        """
                        
                        concepts_result = session.run(concepts_query, video_id=video_id)
                        all_concepts = []
                        for record in concepts_result:
                            concept_name = record["name"]
                            if concept_name:
                                all_concepts.append(concept_name)
                        
                        # 获取一级知识点和二级知识点的关系
                        # 修改查询，获取所有一级知识点对应的扩展知识点（二级知识点）
                        # 注意：二级知识点可能不在当前视频中，不需要要求secondLevel也在视频中
                        relations_query = """
                        MATCH (firstLevel:Concept)-[r:RELATED_TO]->(secondLevel:Concept)
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(firstLevel)
                        RETURN firstLevel.name as first_level, collect(distinct secondLevel.name) as second_level
                        """
                        
                        relations_result = session.run(relations_query, video_id=video_id)
                        
                        # 分析一级知识点和二级知识点
                        primary_concepts = []
                        secondary_concepts = []
                        concept_relations_map = {}
                        
                        for record in relations_result:
                            first_level = record["first_level"]
                            second_level = record["second_level"]
                            
                            if first_level not in primary_concepts:
                                primary_concepts.append(first_level)
                            
                            # 存储一级知识点和其对应的二级知识点的关系
                            concept_relations_map[first_level] = second_level
                            
                            # 收集二级知识点，确保它们不会被当作一级知识点
                            for concept in second_level:
                                if concept not in secondary_concepts and concept not in primary_concepts:
                                    secondary_concepts.append(concept)
                        
                        # 将没有关系的知识点添加为一级知识点
                        for concept in all_concepts:
                            if concept not in primary_concepts and concept not in secondary_concepts:
                                primary_concepts.append(concept)
                                
                        # 重要：确保二级知识点不在all_concepts中，这样它们就不会直接与视频节点相连
                        # 因为我们只希望二级知识点与对应的一级知识点相连
                        for concept in secondary_concepts:
                            if concept in all_concepts:
                                all_concepts.remove(concept)
                        
                        # 记录日志
                        logging.info(f"视频 {video_id} 有 {len(primary_concepts)} 个一级知识点和 {len(secondary_concepts)} 个二级知识点")
                        logging.info(f"一级知识点: {primary_concepts}")
                        logging.info(f"二级知识点: {secondary_concepts}")
                        
                        # 构建节点和连接
                        nodes = []
                        links = []
                        node_ids = set()
                        
                        # 如果没有知识点，返回空图谱
                        if not all_concepts:
                            logging.warning(f"视频 {video_id} 没有知识点")
                            return {"nodes": [], "links": []}
                        
                        # 添加视频节点作为中心
                        video_node = {
                            "id": f"video-{video_id}",
                            "name": video_title,
                            "label": video_title,
                            "main": True,
                            "videoId": video_id,
                            "type": "video",  # 添加类型标记，便于前端区分样式
                            "itemStyle": {"color": "#F472B6"},  # 粉色，与图例说明一致
                            "symbolSize": 60,
                            "expanded": True
                        }
                        nodes.append(video_node)
                        node_ids.add(f"video-{video_id}")
                        
                        # 处理一级知识点（主要知识点）
                        for concept_name in primary_concepts:
                            concept_id = f"concept-{concept_name}"
                            
                            if concept_id not in node_ids:
                                node_data = {
                                    "id": concept_id,
                                    "name": concept_name,
                                    "label": concept_name,
                                    "description": "",
                                    "main": True,
                                    "videoId": video_id,
                                    "type": "primary_concept",  # 添加类型标记
                                    "itemStyle": {"color": "#5470c6"},  # 蓝色
                                    "symbolSize": 40,
                                    "isPrimaryKnowledge": True,
                                    "isFromCurrentVideo": True,
                                    "expanded": True
                                }
                                nodes.append(node_data)
                                node_ids.add(concept_id)
                            
                            # 将视频节点与一级知识点相连
                            links.append({
                                "source": f"video-{video_id}",
                                "target": concept_id,
                                "relationship": "PRIMARY",
                                "lineStyle": {"width": 3, "color": "#5470c6"}
                            })
                        
                        # 处理二级知识点（次要知识点）
                        for concept_name in secondary_concepts:
                            concept_id = f"concept-{concept_name}"
                            
                            if concept_id not in node_ids:
                                node_data = {
                                    "id": concept_id,
                                    "name": concept_name,
                                    "label": concept_name,
                                    "description": "",
                                    "main": False,
                                    "videoId": video_id,
                                    "type": "secondary_concept",  # 添加类型标记
                                    "itemStyle": {"color": "#91cc75"},  # 绿色
                                    "symbolSize": 30,
                                    "isSecondaryKnowledge": True,
                                    "isFromCurrentVideo": True,
                                    "expanded": True
                                }
                                nodes.append(node_data)
                                node_ids.add(concept_id)
                            
                            # 二级知识点仅与对应的一级知识点相连，不与视频节点相连
                        
                        # 添加一级知识点与二级知识点之间的关系
                        for primary in primary_concepts:
                            if primary in concept_relations_map:
                                source_id = f"concept-{primary}"
                                
                                for secondary in concept_relations_map[primary]:
                                    target_id = f"concept-{secondary}"
                                    
                                    # 添加连接
                                    links.append({
                                        "source": source_id,
                                        "target": target_id,
                                        "relationship": "RELATED_TO",
                                        "lineStyle": {"width": 1.5, "color": "#73c0de"}  # 浅蓝色
                                    })
                        
                        # 记录日志
                        logging.info(f"普通视频知识图谱构建完成，节点数: {len(nodes)}，连接数: {len(links)}")
                        
                        # 返回知识图谱数据
                        return {"nodes": nodes, "links": links}
                    except Exception as e:
                        logging.error(f"构建普通视频知识图谱时出错: {str(e)}")
                        return {"nodes": [], "links": []}
                    
                    # 处理二级知识点（次要知识点）
                    for concept_name in secondary_concepts:
                        concept_id = f"concept-{concept_name}"
                        
                        if concept_id not in node_ids:
                            node_data = {
                                "id": concept_id,
                                "name": concept_name,
                                "label": concept_name,
                                "description": "",
                                "main": False,
                                "videoId": video_id,
                                "type": "secondary_concept",  # 添加类型标记
                                "itemStyle": {"color": "#91cc75"},  # 绿色
                                "symbolSize": 30,
                                "isSecondaryKnowledge": True,
                                "isFromCurrentVideo": True,
                                "expanded": True
                            }
                            nodes.append(node_data)
                            node_ids.add(concept_id)
                        
                        # 将视频节点与二级知识点相连
                        links.append({
                            "source": f"video-{video_id}",
                            "target": concept_id,
                            "relationship": "SECONDARY",
                            "lineStyle": {"width": 2, "color": "#91cc75"}
                        })
                    
                    # 处理所有概念关系
                    for concept_relation in record["concept_relations"]:
                        concept = concept_relation["concept"]
                        concept_id = f"concept-{concept['name']}"
                        
                        # 处理RELATED_TO关系
                        for relation in concept_relation["relations"]:
                            if not relation["target"]:
                                continue
                                
                            related_id = f"concept-{relation['target']}"
                            related_node = relation.get("target_node")
                            
                            # 添加关联概念节点
                            if related_id not in node_ids and related_node:
                                node_data = {
                                    "id": related_id,
                                    "name": relation["target"],
                                    "label": relation["target"],
                                    "expanded": True,
                                    "main": False,
                                    "description": related_node.get("description", ""),
                                    "type": "expanded_concept"  # 添加类型标记
                                }
                                
                                # 添加源视频信息（如果有）
                                if related_node.get("source_video_id"):
                                    node_data["source_video_id"] = related_node.get("source_video_id")
                                    node_data["source_video_title"] = related_node.get("source_video_title", "未知视频")
                                
                                nodes.append(node_data)
                                node_ids.add(related_id)
                            
                            # 添加连接
                            links.append({
                                "source": concept_id,
                                "target": related_id,
                                "relationship": relation["relationship"]
                            })
                    
                    logging.info(f"普通视频知识图谱构建完成，节点数: {len(nodes)}，连接数: {len(links)}")
                    return {"nodes": nodes, "links": links}
                
        except Exception as e:
            logger.error(f"获取知识图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {"nodes": [], "links": []}
        finally:
            self.close()
            
    async def generate_knowledge_graph(self, video_id: int, video_title: str, subtitle_text: str, video_tags: List[str] = None) -> bool:
        """生成知识图谱
        
        Args:
            video_id: 视频ID
            video_title: 视频标题
            subtitle_text: 字幕文本
            video_tags: 视频标签列表，默认为空
            
        Returns:
            生成是否成功
        """
        try:
            if not self.connect():
                raise Exception("无法连接到Neo4j数据库")
            
            # 初始化视频标签
            if video_tags is None:
                video_tags = []
            
            logger.info(f"开始为视频 {video_id} 生成知识图谱，标题: {video_title}, 标签: {video_tags}")
            
            # 从字幕文本中提取概念
            logger.info(f"从字幕中提取视频 {video_id} 的概念...")
            concepts = await self.extract_concepts_from_subtitles(subtitle_text)
            logger.info(f"从字幕中提取到 {len(concepts)} 个概念")
            
            if not concepts or len(concepts) == 0:
                logger.error(f"视频 {video_id} 未提取到概念，无法生成知识图谱")
                return False
                
            with self.driver.session() as session:
                # 检查视频节点是否存在，如果存在则删除相关的知识图谱
                logger.info(f"清除视频 {video_id} 的现有知识图谱（如果存在）")
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    OPTIONAL MATCH (v)-[:CONTAINS]->(c:Concept)
                    OPTIONAL MATCH (c)-[r]-()
                    DELETE r, c, v
                    """,
                    video_id=str(video_id)  # 确保视频ID是字符串类型
                )
                
                # 创建视频节点，包含标签
                logger.info(f"创建视频 {video_id} 的节点")
                session.run(
                    """
                    CREATE (v:Video {video_id: $video_id, title: $title, tags: $tags})
                    """,
                    video_id=str(video_id),  # 确保视频ID是字符串类型
                    title=video_title,
                    tags=json.dumps(video_tags, ensure_ascii=False)
                )
                
                # 记录创建的概念数量和关系数量
                concept_count = 0
                relation_count = 0
                
                # 将概念添加到Neo4j
                logger.info(f"开始将 {len(concepts)} 个概念添加到Neo4j数据库")
                for concept in concepts:
                    try:
                        # 创建概念节点
                        session.run(
                            """
                            MERGE (c:Concept {name: $name})
                            ON CREATE SET c.description = $description, c.timestamp = $timestamp
                            WITH c
                            MATCH (v:Video {video_id: $video_id})
                            MERGE (v)-[:CONTAINS]->(c)
                            """,
                            name=concept["name"],
                            description=concept.get("description", ""),
                            timestamp=concept.get("timestamp", 0),
                            video_id=str(video_id)  # 确保视频ID是字符串类型
                        )
                        concept_count += 1
                        
                        # 为每个概念添加扩展知识点
                        if "expanded" in concept and concept["expanded"]:
                            for expanded in concept["expanded"]:
                                session.run(
                                    """
                                    MATCH (c:Concept {name: $concept_name})
                                    MERGE (e:Concept {name: $expanded_name})
                                    ON CREATE SET e.description = $description
                                    MERGE (c)-[:RELATED_TO]->(e)
                                    """,
                                    concept_name=concept["name"],
                                    expanded_name=expanded["name"],
                                    description=expanded.get("description", "")
                                )
                                relation_count += 1
                    except Exception as concept_error:
                        logger.error(f"添加概念 '{concept.get('name', '未知')}' 失败: {str(concept_error)}")
                
                logger.info(f"成功为视频 {video_id} 创建了 {concept_count} 个概念节点和 {relation_count} 个关系")
                
                # 验证知识图谱是否创建成功
                verify_result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN count(c) as concept_count
                    """,
                    video_id=str(video_id)
                ).single()
                
                if verify_result and verify_result["concept_count"] > 0:
                    logger.info(f"验证成功: 视频 {video_id} 的知识图谱包含 {verify_result['concept_count']} 个概念")
                    return True
                else:
                    logger.error(f"验证失败: 视频 {video_id} 的知识图谱未找到概念节点")
                    return False
                
        except Exception as e:
            logger.error(f"生成知识图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.close()
            
    async def extract_concepts_from_subtitles(self, subtitle_text: str) -> List[Dict[str, Any]]:
        """从字幕中提取概念
        
        Args:
            subtitle_text: 字幕文本
            
        Returns:
            概念列表
        """
        try:
            # 使用传入的字幕文本
            full_text = subtitle_text
            
            # 构建提示词
            prompt = f"""
            请从以下视频字幕文本中提取核心知识点概念，并为每个概念提供简短描述和扩展知识点。

            字幕文本：
            {full_text}

            请以JSON格式返回结果，包含以下字段：
            1. name: 概念名称
            2. description: 概念描述
            3. timestamp: 概念在视频中出现的时间点（秒）
            4. expanded: 扩展知识点列表，每个扩展知识点包含name和description字段

            示例格式：
            ```json
            [
              {{
                "name": "梯度下降",
                "description": "一种优化算法，用于最小化损失函数",
                "timestamp": 120,
                "expanded": [
                  {{
                    "name": "随机梯度下降",
                    "description": "梯度下降的变体，每次使用一个样本更新参数"
                  }},
                  {{
                    "name": "批量梯度下降",
                    "description": "使用所有样本计算梯度的梯度下降方法"
                  }}
                ]
              }}
            ]
            ```

            请提取5-10个核心概念，每个概念提供2-3个扩展知识点。确保概念之间有关联性，形成一个连贯的知识网络。
            """
            
            # 先尝试使用Ollama API (方案一)
            concepts = await self._extract_concepts_with_ollama(prompt)
            if concepts:
                return concepts
                
            # 如果Ollama失败，尝试使用在线API (方案二)
            concepts = await self._extract_concepts_with_online_api(prompt)
            if concepts:
                return concepts
                
            # 如果两种方法都失败，返回空列表
            logger.error("所有大语言模型API调用方法都失败")
            return []
                
        except Exception as e:
            logger.error(f"提取概念失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    async def _extract_concepts_with_ollama(self, prompt: str) -> List[Dict[str, Any]]:
        """使用本地Ollama API提取概念
        
        Args:
            prompt: 提示词
            
        Returns:
            概念列表
        """
        try:
            # 调用Ollama API
            response = requests.post(
                f"{OLLAMA_BASE_URL}/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # 降低温度以获得更一致的结果
                        "num_predict": 2048  # 增加生成的token数量
                    }
                },
                timeout=180  # 增加超时时间，从60秒到180秒
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API调用失败: {response.status_code}")
                return []
            
            # 解析响应
            result = response.json()
            response_text = result.get("response", "")
            
            # 提取JSON部分
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text
            
            # 清理JSON字符串
            json_str = re.sub(r'^[^[{]*', '', json_str)
            json_str = re.sub(r'[^}\]]*$', '', json_str)
            
            # 解析JSON
            try:
                concepts = json.loads(json_str)
                logger.info(f"使用Ollama API成功提取了 {len(concepts)} 个概念")
                return concepts
            except json.JSONDecodeError as e:
                logger.error(f"解析Ollama响应的JSON失败: {str(e)}")
                logger.error(f"JSON字符串: {json_str}")
                return []
                
            return []
                
        except Exception as e:
            logger.error(f"使用Ollama API提取概念失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    async def _extract_concepts_with_online_api(self, prompt: str) -> List[Dict[str, Any]]:
        """使用在线API提取概念
        
        Args:
            prompt: 提示词
            
        Returns:
            概念列表
        """
        try:
            # 创建OpenAI客户端
            client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
            
            # 调用OpenAI API
            response = client.chat.completions.create(
                model="qwen-max",  # 使用阿里云的千问模型
                messages=[
                    {"role": "system", "content": "你是一个专业的知识图谱生成助手，擅长从文本中提取核心概念和关系。请严格按照要求的JSON格式返回结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2048
            )
            
            # 获取响应文本
            response_text = response.choices[0].message.content
            
            # 提取JSON部分
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response_text
            
            # 清理JSON字符串
            json_str = re.sub(r'^[^[{]*', '', json_str)
            json_str = re.sub(r'[^}\]]*$', '', json_str)
            
            # 解析JSON
            try:
                concepts = json.loads(json_str)
                logger.info(f"使用在线API成功提取了 {len(concepts)} 个概念")
                return concepts
            except json.JSONDecodeError as e:
                logger.error(f"解析在线API响应的JSON失败: {str(e)}")
                logger.error(f"JSON字符串: {json_str}")
                return []
                
        except Exception as e:
            logger.error(f"使用在线API提取概念失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            

            

            


    def is_combined_video(self, video_id) -> bool:
        """检查视频是否是合并视频
        
        Args:
            video_id: 视频ID
            
        Returns:
            是否是合并视频
        """
        try:
            if not self.connect():
                logger.error("无法连接到Neo4j数据库")
                return False
                
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.is_combined as is_combined
                    """,
                    video_id=str(video_id)
                )
                
                record = result.single()
                if record and record.get('is_combined'):
                    return True
                    
                # 检查视频ID格式是否为 "x_y" 形式
                if isinstance(video_id, str) and "_" in video_id:
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"检查视频是否是合并视频失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.close()
            
    def find_combined_video_id(self, video_id) -> Optional[str]:
        """查找视频参与的合并视频ID
        
        Args:
            video_id: 视频ID
            
        Returns:
            合并视频ID，如果没有则返回None
        """
        try:
            if not self.connect():
                logger.error("无法连接到Neo4j数据库")
                return None
                
            with self.driver.session() as session:
                # 查询包含该视频ID的合并视频
                result = session.run(
                    """
                    MATCH (v:Video)
                    WHERE v.is_combined = true AND v.video_id CONTAINS $video_id
                    RETURN v.video_id as combined_id
                    """,
                    video_id=str(video_id)
                )
                
                records = list(result)
                
                if records:
                    # 可能有多个合并视频包含该视频，返回第一个
                    return records[0].get('combined_id')
                    
                return None
                
        except Exception as e:
            logger.error(f"查找视频参与的合并视频ID失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        finally:
            self.close()
            

