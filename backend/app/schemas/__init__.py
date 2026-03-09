"""Pydantic schemas for request/response validation"""
from app.schemas.video import (
    VideoCreate,
    VideoResponse,
    VideoListResponse,
    VideoStatusResponse,
    VideoUploadResponse,
    VideoProcessRequest,
)
from app.schemas.subtitle import (
    SubtitleResponse,
    SubtitleUpdate,
    SubtitleListResponse,
)
from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    TimestampCreate,
    SimilarNotesRequest,
)
from app.schemas.qa import (
    QuestionCreate,
    QuestionResponse,
    QAHistoryResponse,
)
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.schemas.knowledge_graph import (
    KnowledgeGraphResponse,
    GenerateQuestionsRequest,
    QuestionsResponse,
)

__all__ = [
    # Video
    "VideoCreate",
    "VideoResponse",
    "VideoListResponse",
    "VideoStatusResponse",
    "VideoUploadResponse",
    "VideoProcessRequest",
    # Subtitle
    "SubtitleResponse",
    "SubtitleUpdate",
    "SubtitleListResponse",
    # Note
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    "NoteListResponse",
    "TimestampCreate",
    "SimilarNotesRequest",
    # QA
    "QuestionCreate",
    "QuestionResponse",
    "QAHistoryResponse",
    # Auth
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    # Knowledge Graph
    "KnowledgeGraphResponse",
    "GenerateQuestionsRequest",
    "QuestionsResponse",
]
