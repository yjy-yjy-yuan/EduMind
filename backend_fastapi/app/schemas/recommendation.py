"""视频推荐相关 Schema。"""

from datetime import datetime
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class RecommendationSceneOption(BaseModel):
    """推荐场景描述。"""

    value: str = Field(..., description="场景标识")
    label: str = Field(..., description="场景名称")
    description: str = Field(..., description="场景说明")
    requires_seed: bool = Field(default=False, description="是否需要 seed_video_id")


class RecommendationSceneListResponse(BaseModel):
    """推荐场景列表响应。"""

    message: str
    scenes: List[RecommendationSceneOption] = Field(default_factory=list)


class RecommendationVideoItem(BaseModel):
    """推荐视频条目。"""

    id: Union[int, str]
    title: Optional[str] = None
    status: str = ""
    upload_time: Optional[datetime] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    process_progress: float = 0
    current_step: str = ""
    processing_origin: Optional[str] = None
    processing_origin_label: Optional[str] = None
    upload_source: Optional[str] = None
    upload_source_label: Optional[str] = None
    recommendation_score: float = 0
    reason_code: str = Field(default="recent", description="推荐理由代码")
    reason_label: str = Field(default="推荐", description="推荐理由短标签")
    reason_text: str = Field(default="", description="推荐说明")
    is_external: bool = False
    item_type: Optional[str] = None
    source_label: Optional[str] = None
    external_source_label: Optional[str] = None
    external_url: Optional[str] = None
    subject: Optional[str] = None
    cluster_key: Optional[str] = None
    author: Optional[str] = None


class VideoRecommendationResponse(BaseModel):
    """推荐视频列表响应。"""

    message: str
    scene: str
    strategy: str
    personalized: bool = False
    fallback_used: bool = False
    seed_video_id: Optional[int] = None
    seed_video_title: Optional[str] = None
    items: List[RecommendationVideoItem] = Field(default_factory=list)
