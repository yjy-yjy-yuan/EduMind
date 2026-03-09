"""知识图谱相关的 Pydantic schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field


class KnowledgeGraphNode(BaseModel):
    """知识图谱节点"""
    id: str
    label: str
    type: str
    properties: Optional[dict] = None


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边"""
    source: str
    target: str
    type: str
    properties: Optional[dict] = None


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应"""
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]


class GenerateQuestionsRequest(BaseModel):
    """生成问题请求"""
    concept: str = Field(..., min_length=1, description="知识点")
    context: str = Field(default="", description="背景信息")
    count: int = Field(default=3, ge=1, le=10)
    use_ollama: bool = Field(default=True)


class QuestionsResponse(BaseModel):
    """问题响应"""
    questions: List[str]


class CombineKnowledgeGraphsRequest(BaseModel):
    """合并知识图谱请求"""
    source_video_id: int
    target_video_id: int
    force_combine: bool = False
    threshold: float = Field(default=0.7, ge=0, le=1)


class CombineMultipleRequest(BaseModel):
    """合并多个知识图谱请求"""
    video_ids: List[int] = Field(..., min_length=2)
    threshold: float = Field(default=0.7, ge=0, le=1)
    force_combine: bool = False


class SimilarVideoResponse(BaseModel):
    """相似视频响应"""
    id: int
    title: str
    similarity: float
    tags: List[str]
