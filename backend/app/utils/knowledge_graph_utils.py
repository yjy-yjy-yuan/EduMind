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
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="cjx20040328"):
        """初始化知识图谱管理器"""
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
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
            
    def combine_knowledge_graphs(self, source_video_id: int, target_video_id: int) -> bool:
        """整合两个视频的知识图谱
        
        Args:
            source_video_id: 源视频ID
            target_video_id: 目标视频ID
            
        Returns:
            整合是否成功
        """
        try:
            if not self.connect():
                raise Exception("无法连接到Neo4j数据库")
                
            with self.driver.session() as session:
                # 1. 检查两个视频节点是否存在
                source_exists = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN count(v) > 0 as exists
                    """,
                    video_id=source_video_id
                ).single()["exists"]
                
                target_exists = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN count(v) > 0 as exists
                    """,
                    video_id=target_video_id
                ).single()["exists"]
                
                if not source_exists:
                    logger.error(f"源视频节点不存在: {source_video_id}")
                    return False
                    
                if not target_exists:
                    logger.error(f"目标视频节点不存在: {target_video_id}")
                    return False
                
                # 2. 获取两个视频的标签和标题
                source_data = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.title as title, v.tags as tags
                    """,
                    video_id=source_video_id
                ).single()
                
                target_data = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.title as title, v.tags as tags
                    """,
                    video_id=target_video_id
                ).single()
                
                source_title = source_data["title"]
                target_title = target_data["title"]
                
                # 3. 合并标签
                source_tags = []
                target_tags = []
                
                if source_data["tags"]:
                    try:
                        source_tags = json.loads(source_data["tags"])
                    except json.JSONDecodeError:
                        logger.warning(f"源视频 {source_video_id} 的标签格式无效: {source_data['tags']}")
                        
                if target_data["tags"]:
                    try:
                        target_tags = json.loads(target_data["tags"])
                    except json.JSONDecodeError:
                        logger.warning(f"目标视频 {target_video_id} 的标签格式无效: {target_data['tags']}")
                
                # 合并标签并去重
                combined_tags = list(set(source_tags + target_tags))
                
                # 4. 创建整合后的视频节点
                combined_title = f"{source_title} + {target_title}"
                combined_video_id = f"combined_{source_video_id}_{target_video_id}"
                
                # 删除可能存在的旧的整合节点
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    OPTIONAL MATCH (v)-[:CONTAINS]->(c:Concept)
                    OPTIONAL MATCH (c)-[r]->()
                    DELETE r, c, v
                    """,
                    video_id=combined_video_id
                )
                
                # 创建新的整合节点
                session.run(
                    """
                    CREATE (v:Video {video_id: $video_id, title: $title, tags: $tags, is_combined: true})
                    """,
                    video_id=combined_video_id,
                    title=combined_title,
                    tags=json.dumps(combined_tags, ensure_ascii=False)
                )
                
                # 5. 复制源视频的概念到整合节点
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})-[:CONTAINS]->(concept:Concept)
                    MATCH (target:Video {video_id: $target_id})
                    MERGE (target)-[:CONTAINS]->(concept)
                    """,
                    source_id=source_video_id,
                    target_id=combined_video_id
                )
                
                # 6. 复制目标视频的概念到整合节点
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})-[:CONTAINS]->(concept:Concept)
                    MATCH (target:Video {video_id: $target_id})
                    MERGE (target)-[:CONTAINS]->(concept)
                    """,
                    source_id=target_video_id,
                    target_id=combined_video_id
                )
                
                # 7. 创建源视频和目标视频与整合节点的关系
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})
                    MATCH (combined:Video {video_id: $combined_id})
                    MERGE (source)-[:COMBINED_INTO]->(combined)
                    """,
                    source_id=source_video_id,
                    combined_id=combined_video_id
                )
                
                session.run(
                    """
                    MATCH (source:Video {video_id: $source_id})
                    MATCH (combined:Video {video_id: $combined_id})
                    MERGE (source)-[:COMBINED_INTO]->(combined)
                    """,
                    source_id=target_video_id,
                    combined_id=combined_video_id
                )
                
                logger.info(f"成功整合视频 {source_video_id} 和视频 {target_video_id} 的知识图谱")
                return True
                
        except Exception as e:
            logger.error(f"整合知识图谱失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            self.close()
            
    def get_knowledge_graph(self, video_id: int) -> Dict[str, Any]:
        """获取视频的知识图谱
        
        Args:
            video_id: 视频ID
            
        Returns:
            包含节点和连接的知识图谱数据
        """
        try:
            if not self.connect():
                raise Exception("无法连接到Neo4j数据库")
                
            with self.driver.session() as session:
                # 查询与视频相关的知识点
                query = """
                MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                OPTIONAL MATCH (c)-[r:RELATED_TO]->(related:Concept)
                RETURN c, collect(distinct {target: related.name, relationship: type(r)}) as relations
                """
                
                result = session.run(query, video_id=video_id)
                records = list(result)
                
                if not records:
                    return {"nodes": [], "links": []}
                
                # 构建节点和连接
                nodes = []
                links = []
                node_ids = set()
                
                for record in records:
                    concept = record["c"]
                    concept_id = f"concept-{concept['name']}"
                    
                    # 添加主概念节点
                    if concept_id not in node_ids:
                        nodes.append({
                            "id": concept_id,
                            "label": concept["name"],
                            "description": concept.get("description", ""),
                            "main": True,
                            "videoId": video_id,
                            "timestamp": concept.get("timestamp", 0)
                        })
                        node_ids.add(concept_id)
                    
                    # 添加关联概念和连接
                    for relation in record["relations"]:
                        if not relation["target"]:
                            continue
                            
                        related_id = f"concept-{relation['target']}"
                        
                        # 添加关联概念节点
                        if related_id not in node_ids:
                            nodes.append({
                                "id": related_id,
                                "label": relation["target"],
                                "expanded": True,
                                "main": False
                            })
                            node_ids.add(related_id)
                        
                        # 添加连接
                        links.append({
                            "source": concept_id,
                            "target": related_id,
                            "relationship": relation["relationship"]
                        })
                
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
                
            with self.driver.session() as session:
                # 检查视频节点是否存在，如果存在则删除相关的知识图谱
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    OPTIONAL MATCH (v)-[:CONTAINS]->(c:Concept)
                    OPTIONAL MATCH (c)-[r]-()
                    DELETE r, c, v
                    """,
                    video_id=video_id
                )
                
                # 初始化视频标签
                if video_tags is None:
                    video_tags = []
                
                logger.info(f"为视频 {video_id} 创建知识图谱节点，标签: {video_tags}")
                
                # 创建视频节点，包含标签
                session.run(
                    """
                    CREATE (v:Video {video_id: $video_id, title: $title, tags: $tags})
                    """,
                    video_id=video_id,
                    title=video_title,
                    tags=json.dumps(video_tags, ensure_ascii=False)
                )
                
                # 从字幕文本中提取概念
                concepts = await self.extract_concepts_from_subtitles(subtitle_text)
                
                # 将概念添加到Neo4j
                for concept in concepts:
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
                        video_id=video_id
                    )
                    
                    # 为每个概念添加扩展知识点
                    if "expanded" in concept and concept["expanded"]:
                        for expanded in concept["expanded"]:
                            session.run(
                                """
                                MERGE (c:Concept {name: $concept_name})
                                MERGE (e:Concept {name: $expanded_name})
                                ON CREATE SET e.description = $description
                                MERGE (c)-[:RELATED_TO]->(e)
                                """,
                                concept_name=concept["name"],
                                expanded_name=expanded["name"],
                                description=expanded.get("description", "")
                            )
                
                return True
                
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
                timeout=60  # 增加超时时间
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
            
    async def search_related_videos(self, keyword: str, video_type: str, expanded: List[str] = None) -> List[Dict[str, Any]]:
        """搜索相关视频
        
        Args:
            keyword: 关键词
            video_type: 视频类型，'basic'或'advanced'
            expanded: 扩展知识点列表
            
        Returns:
            相关视频列表
        """
        try:
            # 构建搜索关键词
            if video_type == "basic":
                # 基础讲解搜索
                search_query = f"{keyword} 基础 教程"
            else:
                # 进阶搜索，结合扩展知识点
                expanded_terms = " ".join(expanded[:3]) if expanded else ""
                search_query = f"{keyword} {expanded_terms} 进阶 深入"
            
            # 搜索B站视频
            bilibili_videos = await self.search_bilibili_videos(search_query)
            
            # 搜索YouTube视频
            youtube_videos = await self.search_youtube_videos(search_query)
            
            # 合并结果并限制数量
            all_videos = bilibili_videos + youtube_videos
            result_videos = all_videos[:5]  # 最多返回5个视频
            
            return result_videos
            
        except Exception as e:
            logger.error(f"搜索视频失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
            
    async def search_bilibili_videos(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索B站视频
        
        Args:
            keyword: 关键词
            
        Returns:
            B站视频列表
        """
        try:
            # 模拟B站搜索API调用
            # 实际实现中应该使用B站的API
            # 这里使用模拟数据
            return [
                {
                    "title": f"{keyword} - B站教程1",
                    "url": f"https://www.bilibili.com/video/BV1xx411c7mD",
                    "source": "哔哩哔哩",
                    "duration": "10:30"
                },
                {
                    "title": f"{keyword} - B站教程2",
                    "url": f"https://www.bilibili.com/video/BV1xx411c7mE",
                    "source": "哔哩哔哩",
                    "duration": "15:45"
                }
            ]
        except Exception as e:
            logger.error(f"搜索B站视频失败: {str(e)}")
            return []
            
    async def search_youtube_videos(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索YouTube视频
        
        Args:
            keyword: 关键词
            
        Returns:
            YouTube视频列表
        """
        try:
            # 模拟YouTube搜索API调用
            # 实际实现中应该使用YouTube的API
            # 这里使用模拟数据
            return [
                {
                    "title": f"{keyword} - YouTube Tutorial 1",
                    "url": f"https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "source": "YouTube",
                    "duration": "8:20"
                },
                {
                    "title": f"{keyword} - YouTube Tutorial 2",
                    "url": f"https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "source": "YouTube",
                    "duration": "12:15"
                }
            ]
        except Exception as e:
            logger.error(f"搜索YouTube视频失败: {str(e)}")
            return []
