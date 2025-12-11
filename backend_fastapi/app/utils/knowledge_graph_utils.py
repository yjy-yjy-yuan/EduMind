"""知识图谱工具 - FastAPI 版本

用于构建和管理视频知识图谱，使用 Neo4j 存储
"""

import json
import logging
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import requests
from app.core.config import settings
from neo4j import GraphDatabase
from openai import OpenAI

logger = logging.getLogger(__name__)


class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
    ):
        """初始化知识图谱管理器"""
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.driver = None

    def connect(self) -> bool:
        """连接 Neo4j 数据库"""
        try:
            if self.driver is None:
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            return True
        except Exception as e:
            logger.error(f"Neo4j 连接失败: {str(e)}")
            return False

    def close(self):
        """关闭 Neo4j 连接"""
        if self.driver:
            self.driver.close()
            self.driver = None

    def build_from_subtitle(self, video_id: int, subtitle_content: str, rebuild: bool = False) -> dict:
        """从字幕构建知识图谱

        Args:
            video_id: 视频 ID
            subtitle_content: 字幕内容
            rebuild: 是否重建

        Returns:
            构建结果
        """
        try:
            if not self.connect():
                raise Exception("无法连接到 Neo4j 数据库")

            video_id_str = str(video_id)

            with self.driver.session() as session:
                # 如果重建，先删除现有图谱
                if rebuild:
                    session.run(
                        """
                        MATCH (v:Video {video_id: $video_id})
                        OPTIONAL MATCH (v)-[:CONTAINS]->(c:Concept)
                        OPTIONAL MATCH (c)-[r]-()
                        DELETE r, c, v
                        """,
                        video_id=video_id_str,
                    )

                # 提取概念
                concepts = self._extract_concepts(subtitle_content)
                if not concepts:
                    return {"node_count": 0, "edge_count": 0}

                # 创建视频节点
                session.run(
                    """
                    MERGE (v:Video {video_id: $video_id})
                    ON CREATE SET v.title = $title
                    """,
                    video_id=video_id_str,
                    title=f"视频 {video_id}",
                )

                node_count = 0
                edge_count = 0

                # 创建概念节点和关系
                for concept in concepts:
                    session.run(
                        """
                        MERGE (c:Concept {name: $name})
                        ON CREATE SET c.description = $description
                        WITH c
                        MATCH (v:Video {video_id: $video_id})
                        MERGE (v)-[:CONTAINS]->(c)
                        """,
                        name=concept["name"],
                        description=concept.get("description", ""),
                        video_id=video_id_str,
                    )
                    node_count += 1

                    # 添加扩展知识点
                    for expanded in concept.get("expanded", []):
                        session.run(
                            """
                            MATCH (c:Concept {name: $concept_name})
                            MERGE (e:Concept {name: $expanded_name})
                            ON CREATE SET e.description = $description
                            MERGE (c)-[:RELATED_TO]->(e)
                            """,
                            concept_name=concept["name"],
                            expanded_name=expanded["name"],
                            description=expanded.get("description", ""),
                        )
                        edge_count += 1

                return {"node_count": node_count, "edge_count": edge_count}

        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise
        finally:
            self.close()

    def _extract_concepts(self, text: str) -> List[dict]:
        """从文本中提取概念"""
        prompt = f"""
请从以下视频字幕文本中提取核心知识点概念，并为每个概念提供简短描述和扩展知识点。

字幕文本：
{text[:3000]}

请以 JSON 格式返回结果：
```json
[
  {{
    "name": "概念名称",
    "description": "概念描述",
    "expanded": [
      {{"name": "扩展知识点", "description": "描述"}}
    ]
  }}
]
```

请提取 5-10 个核心概念，每个概念提供 2-3 个扩展知识点。
"""

        # 尝试使用 Ollama
        try:
            response = requests.post(
                f"{settings.OLLAMA_BASE_URL}/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=180,
            )

            if response.status_code == 200:
                response_text = response.json().get("response", "")
                return self._parse_concepts_json(response_text)
        except Exception as e:
            logger.warning(f"Ollama 提取概念失败: {str(e)}")

        # 尝试使用在线 API
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
            response = client.chat.completions.create(
                model="qwen-max",
                messages=[
                    {"role": "system", "content": "你是一个专业的知识图谱生成助手。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            response_text = response.choices[0].message.content
            return self._parse_concepts_json(response_text)
        except Exception as e:
            logger.error(f"在线 API 提取概念失败: {str(e)}")
            return []

    def _parse_concepts_json(self, response_text: str) -> List[dict]:
        """解析概念 JSON"""
        try:
            # 提取 JSON 部分
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text

            # 清理 JSON 字符串
            json_str = re.sub(r"^[^[{]*", "", json_str)
            json_str = re.sub(r"[^}\]]*$", "", json_str)

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"解析概念 JSON 失败: {str(e)}")
            return []

    def query(self, query_text: str, video_id: int = None, limit: int = 10) -> List[dict]:
        """查询知识图谱"""
        try:
            if not self.connect():
                return []

            with self.driver.session() as session:
                if video_id:
                    result = session.run(
                        """
                        MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                        WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                        RETURN c.name as name, c.description as description
                        LIMIT $limit
                        """,
                        video_id=str(video_id),
                        query=query_text,
                        limit=limit,
                    )
                else:
                    result = session.run(
                        """
                        MATCH (c:Concept)
                        WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                        RETURN c.name as name, c.description as description
                        LIMIT $limit
                        """,
                        query=query_text,
                        limit=limit,
                    )

                return [{"name": r["name"], "description": r["description"]} for r in result]

        except Exception as e:
            logger.error(f"查询知识图谱失败: {str(e)}")
            return []
        finally:
            self.close()

    def get_video_graph(self, video_id: int) -> dict:
        """获取视频的知识图谱数据"""
        try:
            if not self.connect():
                return {"nodes": [], "edges": []}

            video_id_str = str(video_id)

            with self.driver.session() as session:
                # 获取视频信息
                video_result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    RETURN v.title as title
                    """,
                    video_id=video_id_str,
                ).single()

                if not video_result:
                    return {"nodes": [], "edges": []}

                nodes = []
                edges = []
                node_ids = set()

                # 添加视频节点
                video_node_id = f"video-{video_id}"
                nodes.append(
                    {
                        "id": video_node_id,
                        "name": video_result["title"] or f"视频 {video_id}",
                        "type": "video",
                        "symbolSize": 60,
                        "itemStyle": {"color": "#F472B6"},
                    }
                )
                node_ids.add(video_node_id)

                # 获取一级概念
                concepts_result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    RETURN c.name as name, c.description as description
                    """,
                    video_id=video_id_str,
                )

                for record in concepts_result:
                    concept_id = f"concept-{record['name']}"
                    if concept_id not in node_ids:
                        nodes.append(
                            {
                                "id": concept_id,
                                "name": record["name"],
                                "description": record["description"] or "",
                                "type": "primary_concept",
                                "symbolSize": 40,
                                "itemStyle": {"color": "#5470c6"},
                            }
                        )
                        node_ids.add(concept_id)

                        # 添加视频到概念的边
                        edges.append(
                            {
                                "source": video_node_id,
                                "target": concept_id,
                                "relationship": "CONTAINS",
                            }
                        )

                # 获取概念间关系
                relations_result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c1:Concept)
                    MATCH (c1)-[:RELATED_TO]->(c2:Concept)
                    RETURN c1.name as source, c2.name as target, c2.description as description
                    """,
                    video_id=video_id_str,
                )

                for record in relations_result:
                    target_id = f"concept-{record['target']}"
                    if target_id not in node_ids:
                        nodes.append(
                            {
                                "id": target_id,
                                "name": record["target"],
                                "description": record["description"] or "",
                                "type": "secondary_concept",
                                "symbolSize": 30,
                                "itemStyle": {"color": "#91cc75"},
                            }
                        )
                        node_ids.add(target_id)

                    edges.append(
                        {
                            "source": f"concept-{record['source']}",
                            "target": target_id,
                            "relationship": "RELATED_TO",
                        }
                    )

                return {"nodes": nodes, "edges": edges}

        except Exception as e:
            logger.error(f"获取视频知识图谱失败: {str(e)}")
            return {"nodes": [], "edges": []}
        finally:
            self.close()

    def get_status(self, video_id: int) -> dict:
        """获取知识图谱状态"""
        try:
            if not self.connect():
                return {"status": "error", "node_count": 0, "edge_count": 0}

            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})-[:CONTAINS]->(c:Concept)
                    OPTIONAL MATCH (c)-[r:RELATED_TO]->()
                    RETURN count(DISTINCT c) as node_count, count(r) as edge_count
                    """,
                    video_id=str(video_id),
                ).single()

                if result and result["node_count"] > 0:
                    return {
                        "status": "ready",
                        "node_count": result["node_count"],
                        "edge_count": result["edge_count"],
                    }
                return {"status": "empty", "node_count": 0, "edge_count": 0}

        except Exception as e:
            logger.error(f"获取知识图谱状态失败: {str(e)}")
            return {"status": "error", "node_count": 0, "edge_count": 0}
        finally:
            self.close()

    def delete_video_graph(self, video_id: int):
        """删除视频的知识图谱"""
        try:
            if not self.connect():
                return

            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (v:Video {video_id: $video_id})
                    OPTIONAL MATCH (v)-[:CONTAINS]->(c:Concept)
                    OPTIONAL MATCH (c)-[r]-()
                    DELETE r, c, v
                    """,
                    video_id=str(video_id),
                )

        except Exception as e:
            logger.error(f"删除知识图谱失败: {str(e)}")
            raise
        finally:
            self.close()

    def get_all_concepts(self, limit: int = 50) -> List[dict]:
        """获取所有概念"""
        try:
            if not self.connect():
                return []

            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Concept)
                    RETURN c.name as name, c.description as description
                    LIMIT $limit
                    """,
                    limit=limit,
                )

                return [{"name": r["name"], "description": r["description"]} for r in result]

        except Exception as e:
            logger.error(f"获取概念列表失败: {str(e)}")
            return []
        finally:
            self.close()

    def get_related_concepts(self, concept: str, depth: int = 1) -> List[dict]:
        """获取相关概念"""
        try:
            if not self.connect():
                return []

            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (c:Concept {name: $concept})-[:RELATED_TO*1..$depth]->(related:Concept)
                    RETURN DISTINCT related.name as name, related.description as description
                    """,
                    concept=concept,
                    depth=depth,
                )

                return [{"name": r["name"], "description": r["description"]} for r in result]

        except Exception as e:
            logger.error(f"获取相关概念失败: {str(e)}")
            return []
        finally:
            self.close()
