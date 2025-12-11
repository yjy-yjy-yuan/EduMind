"""知识图谱 Pydantic Schema"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class KnowledgeGraphBuildRequest(BaseModel):
    """构建知识图谱请求"""

    video_id: int
    rebuild: bool = Field(default=False, description="是否重新构建")


class KnowledgeGraphQueryRequest(BaseModel):
    """知识图谱查询请求"""

    query: str = Field(..., min_length=1)
    video_id: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=100)


class GraphNode(BaseModel):
    """图节点"""

    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """图边"""

    source: str
    target: str
    label: str
    properties: Dict[str, Any] = {}


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应"""

    message: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    video_id: Optional[int] = None


class KnowledgeGraphStatusResponse(BaseModel):
    """知识图谱状态响应"""

    video_id: int
    status: str
    node_count: int
    edge_count: int
