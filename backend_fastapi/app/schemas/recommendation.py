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
    provider: Optional[str] = None
    can_import: bool = False
    import_hint: Optional[str] = None
    action_type: Optional[str] = None
    action_label: Optional[str] = None
    action_target: Optional[str] = None
    action_api: Optional[str] = None
    action_method: Optional[str] = None


class RecommendationSourceItem(BaseModel):
    """推荐来源统计。"""

    source_type: str = Field(..., description="internal/external")
    provider: str = Field(..., description="来源 provider 标识")
    source_label: str = Field(..., description="来源展示名称")
    count: int = Field(default=0, description="当前返回结果中该来源条目数")


class RecommendationExternalQuery(BaseModel):
    """站外候选检索摘要。"""

    query_text: str = Field(default="", description="站外检索关键词")
    subject: str = Field(default="", description="本次检索聚焦科目")
    primary_topic: str = Field(default="", description="本次检索主主题")
    preferred_tags: List[str] = Field(default_factory=list, description="优先标签")
    preferred_provider: str = Field(default="", description="相关推荐优先来源 provider")
    preferred_provider_label: str = Field(default="", description="相关推荐优先来源展示名称")


class RecommendationExternalProviderItem(BaseModel):
    """站外 provider 抓取摘要。"""

    provider: str = Field(..., description="provider 标识")
    source_label: str = Field(..., description="provider 展示名称")
    status: str = Field(default="success", description="success/empty/failed")
    candidate_count: int = Field(default=0, description="本次抓取产出的候选条数")
    error_message: str = Field(default="", description="失败摘要")
    latency_ms: int = Field(default=0, description="抓取耗时（毫秒）")


class VideoRecommendationResponse(BaseModel):
    """推荐视频列表响应。"""

    message: str
    contract_version: str = Field(default="1", description="Recommendation Contract 版本号，用于渐进升级与灰度观测")
    scene: str
    strategy: str
    personalized: bool = False
    fallback_used: bool = False
    seed_video_id: Optional[int] = None
    seed_video_title: Optional[str] = None
    internal_item_count: int = 0
    external_item_count: int = 0
    external_failed_provider_count: int = 0
    external_fetch_failed: bool = False
    coach_summary: Optional[str] = Field(default=None, description="可选：模板或 LLM 一句话说明，默认不返回")
    sources: List[RecommendationSourceItem] = Field(default_factory=list)
    external_query: Optional[RecommendationExternalQuery] = None
    external_providers: List[RecommendationExternalProviderItem] = Field(default_factory=list)
    items: List[RecommendationVideoItem] = Field(default_factory=list)
