# EduMind Backend Architecture Overview

> Note
> This document contains legacy Flask-era architecture notes. Knowledge graph and Neo4j-related sections are obsolete and were removed from the active FastAPI/iOS product chain on 2026-03-16.

## Executive Summary

EduMind is an intelligent educational video processing and knowledge extraction platform built with Flask, featuring automated video transcription, knowledge graph generation, and AI-powered question-answering capabilities. The backend uses Celery for async task processing, Neo4j for knowledge graph storage, and multiple LLM integrations for content analysis.

---

## 1. Flask Application Structure

### 1.1 Application Factory Pattern
**File**: `/backend/app/__init__.py`

The application uses the Flask application factory pattern for clean initialization and configuration management:

```
Application Initialization Flow:
create_app(config_name='default')
  ├── Load configuration from config.py
  ├── Initialize extensions (SQLAlchemy, Migrate, CORS, Celery)
  ├── Configure file upload directories (uploads/, previews/, subtitles/)
  ├── Create database tables via db.create_all()
  └── Register all blueprints with respective URL prefixes
```

### 1.2 Core Extensions
**File**: `/backend/app/extensions.py`

Initialized extensions:
- **SQLAlchemy (db)**: SQL database ORM for relational data (MySQL)
- **Flask-Migrate (migrate)**: Database schema versioning and migrations
- **Flask-CORS (cors)**: Cross-origin request handling for frontend at http://localhost:328
- **Celery**: Asynchronous task queue for long-running operations (Redis broker/backend)

**Platform-Specific Configuration**:
- Mac systems use `solo` worker pool with both standard and MPS-optimized task modules
- Linux/Windows use `prefork` worker pool with standard task modules

### 1.3 Blueprints & Route Organization
**File**: `/backend/app/routes/__init__.py`

```
Route Blueprints:
├── /api/videos → video_bp (video upload, processing, management)
├── /api/subtitles → subtitle_bp (subtitle extraction, management)
├── /api/notes → note_bp (user notes and annotations)
├── /api/qa → qa_bp (question answering system)
├── /api/auth → auth_bp (user authentication)
├── /api/knowledge-graph → knowledge_graph_router (graph queries)
└── /api/knowledge-graph-integration → integration_bp (graph construction)
```

---

## 2. Database Models & Relationships

### 2.1 Core Data Models

#### Video Model
**File**: `/backend/app/models/video.py`

Primary entity representing uploaded videos with processing metadata:

```python
Video
  ├── Basic Info: id, title, filename, filepath, url
  ├── Processing State: status (UPLOADED→PENDING→PROCESSING→COMPLETED/FAILED)
  ├── Progress Tracking: process_progress (0-100%), current_step, task_id
  ├── Video Metadata: duration, fps, width, height, frame_count, md5
  ├── Generated Content: preview_filepath, processed_filepath, subtitle_filepath
  ├── AI Output: summary (video abstract), tags (JSON)
  └── Relationships:
      ├── has many Subtitles
      ├── has many Notes
      └── has many Questions
```

**Status Enum Values**:
- `UPLOADED`: Initial state after file upload
- `PENDING`: Queued for processing
- `PROCESSING`: Currently being processed
- `COMPLETED`: Successfully processed
- `FAILED`: Processing error occurred
- `DOWNLOADING`: For video URL-based uploads

#### Subtitle Model
**File**: `/backend/app/models/subtitle.py`

Time-synchronized subtitle segments from transcription or extraction:

```python
Subtitle
  ├── video_id (FK) → Video
  ├── Time: start_time, end_time (in seconds)
  ├── Content: text (transcribed or extracted)
  ├── Metadata: source (asr/extract/manual), language (zh/en/etc)
  ├── Timestamps: created_at, updated_at
  └── Methods: to_srt() for SRT format export
```

#### Note Model
**File**: `/backend/app/models/note.py`

User-created study notes with semantic analysis:

```python
Note
  ├── id, title, content (plaintext)
  ├── note_type (text/code/list)
  ├── video_id (FK, optional) → Video
  ├── content_vector (embeddings in JSON)
  ├── tags, keywords (auto-extracted)
  ├── created_at, updated_at
  └── Relationships:
      └── has many NoteTimestamps (links to specific video seconds)

NoteTimestamp
  ├── note_id (FK) → Note
  ├── time_seconds (video position)
  └── subtitle_text (associated subtitle)
```

#### Question Model
**File**: `/backend/app/models/qa.py`

Q&A pairs for video-specific and free-form questions:

```python
Question
  ├── video_id (FK, nullable) → Video (NULL for free-form QA)
  ├── content (question text)
  ├── answer (LLM-generated response)
  └── Timestamps: created_at, updated_at
```

#### User Model
**File**: `/backend/app/models/user.py`

User account and profile management:

```python
User
  ├── Authentication: id, username, email, password_hash
  ├── Profile: gender, education, occupation, learning_direction
  ├── Media: avatar (URL), bio
  └── Timestamps: created_at, last_login
```

### 2.2 Database Configuration
**File**: `/backend/config.py`

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Qw242015@localhost/edumind'
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

---

## 3. Asynchronous Task Processing (Celery)

### 3.1 Celery Configuration
**File**: `/backend/celery_app.py`

```
Celery Setup:
├── Broker: Redis (localhost:6379/0) - Task queue
├── Backend: Redis (localhost:6379/0) - Result storage
├── Task Modules:
│   ├── app.tasks.video_processing (standard version)
│   ├── app.tasks.video_processing_mac (Mac MPS optimization)
│   ├── app.tasks.audio_processing (audio extraction)
│   └── app.tasks.subtitle_tasks (subtitle processing)
├── Worker Pool: 'solo' (Mac) / 'prefork' (Linux/Windows)
├── Task Timeout: 3 hours (10800s)
├── Result Expiry: 1 hour (3600s)
└── Serialization: JSON (for cross-platform compatibility)
```

### 3.2 Video Processing Pipeline

**File**: `/backend/app/tasks/video_processing.py`

Main async task: `process_video(video_id, language='zh', model='turbo')`

```
Video Processing Workflow:
┌─────────────────────────────────────────────────────────┐
│ 1. PREVIEW GENERATION (10% progress)                    │
│    └─ Extract first frame using OpenCV                  │
│       └─ Save as preview_X.jpg in previews/             │
├─────────────────────────────────────────────────────────┤
│ 2. VIDEO METADATA EXTRACTION (20% progress)             │
│    └─ Use FFmpeg to get:                                │
│       ├─ Duration, FPS, resolution (width×height)       │
│       ├─ Frame count, codec info                        │
│       └─ Store in Video.duration, .fps, .width, etc     │
├─────────────────────────────────────────────────────────┤
│ 3. AUDIO EXTRACTION (30% progress)                      │
│    ├─ Extract audio stream using FFmpeg                 │
│    ├─ Convert to WAV format (16-bit, 16kHz)             │
│    └─ Save to temp directory                            │
├─────────────────────────────────────────────────────────┤
│ 4. SPEECH-TO-TEXT TRANSCRIPTION (50% progress)          │
│    ├─ Load OpenAI Whisper model (base/small/medium...)  │
│    ├─ For long audio: split into 10-min chunks          │
│    ├─ Transcribe each chunk with language hints         │
│    ├─ Generate Whisper result with timestamps           │
│    └─ GPU/CPU auto-selection (CUDA if available)        │
├─────────────────────────────────────────────────────────┤
│ 5. SUBTITLE FORMATTING (70% progress)                   │
│    ├─ Convert Whisper output to SRT/VTT format          │
│    ├─ Create Subtitle model instances with:             │
│    │   ├─ start_time, end_time (from Whisper)           │
│    │   ├─ text (transcribed), source='asr'              │
│    │   └─ language (from request)                       │
│    └─ Save formatted subtitles to file                  │
├─────────────────────────────────────────────────────────┤
│ 6. CONTENT ANALYSIS (85% progress)                      │
│    ├─ Summary Generation (via summary_generator.py)     │
│    │   ├─ Use Ollama local models (deepseek-r1:8b)      │
│    │   ├─ Fallback to online API (Qwen/OpenAI)          │
│    │   └─ Store in Video.summary                        │
│    │                                                     │
│    └─ Tag Generation (via tag_generator.py)             │
│        ├─ Extract keywords from subtitles               │
│        ├─ Generate topic tags via LLM                   │
│        └─ Store as JSON in Video.tags                   │
├─────────────────────────────────────────────────────────┤
│ 7. FINALIZATION (100% progress)                         │
│    └─ Update Video.status = COMPLETED                   │
│    └─ Commit all changes to database                    │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Key Task Functions

```python
# Main processing task
@celery.task(bind=True)
def process_video(self, video_id, language='zh', model='turbo'):
    # Full video processing pipeline above

# Helper functions
generate_video_info(video_path)           # Extract video metadata
extract_video_info(video)                  # Populate Video model
generate_preview(video_path)               # Create thumbnail
extract_audio_from_video(video_path)       # Audio extraction
transcribe_audio(audio_path, model_name, language)  # Whisper transcription
get_whisper_params(model_name, language)   # Model-specific config
process_long_audio(audio_path, chunk_duration=600)  # Split for parallel processing
merge_transcriptions(chunks_results)       # Combine chunk results
format_subtitles_to_srt(segments)          # SRT format generation
```

---

## 4. Key Service Modules

### 4.1 Summary Generator
**File**: `/backend/services/summary_generator.py`

Generates concise video content summaries using LLMs:

```python
class SummaryGenerator:
  ├── __init__()
  │   └─ Auto-detect Ollama service availability
  │
  ├── _prepare_prompt(subtitle_text) → formatted prompt
  │   └─ Custom system prompt for educational context
  │
  ├── generate_ollama(subtitles) → summary
  │   └─ Local inference via Ollama API
  │
  └─ generate_online(subtitles, api_key) → summary
      └─ Cloud API (Qwen/OpenAI) inference

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "deepseek-r1:8b"
OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 4.2 Tag Generator
**File**: `/backend/services/tag_generator.py`

Extracts and generates topic tags for videos:

**Functions**:
- `extract_keywords(text)` - Keyword extraction from subtitles
- `generate_tags_via_llm(keywords, context)` - LLM-based tag generation
- `store_tags(video_id, tags)` - Persist tags as JSON

### 4.3 LLM Similarity Service
**File**: `/backend/services/llm_similarity_service.py`

Semantic similarity matching for knowledge graph nodes and QA:

**Functions**:
- `compute_embedding(text)` - Generate text embeddings
- `calculate_similarity(text1, text2)` - Semantic similarity score
- `find_similar_nodes(query, graph_nodes, threshold)` - Node matching

### 4.4 Knowledge Graph Utils
**File**: `/backend/app/utils/knowledge_graph_utils.py`

Neo4j-based knowledge graph management:

```python
class KnowledgeGraphManager:
  ├── __init__(uri, user, password) - Neo4j connection
  ├── connect() / close()              - Connection lifecycle
  ├── create_node(label, properties)   - Node creation
  ├── create_relationship(source, rel, target) - Edge creation
  ├── get_knowledge_graph(video_id)    - Retrieve graph structure
  ├── query_graph(cypher_query)        - Raw Cypher queries
  └── merge_graphs(video_ids)          - Combine multiple video graphs
```

### 4.5 QA System
**File**: `/backend/app/utils/qa_utils.py`

Question-answering system with RAG (Retrieval-Augmented Generation):

```python
class QASystem:
  ├── create_knowledge_base(subtitle_filepath) → vectorstore
  │   ├─ Parse subtitle file (SRT/VTT/TXT)
  │   ├─ Split into semantic chunks
  │   └─ Generate embeddings and index
  │
  ├── get_answer(question, api_key, mode='video') → answer
  │   ├─ In 'video' mode: retrieve relevant subtitles (RAG)
  │   ├─ In 'free' mode: direct LLM without retrieval
  │   └─ Send to LLM with context
  │
  └─ get_answer_stream(question, ...) → generator
      └─ Streaming version for real-time response
```

**Configuration**:
- Default model: 'turbo' (fast inference)
- Fallback models: 'small', 'medium', 'large'
- Ollama local inference support
- OpenAI/Qwen API with streaming

---

## 5. API Route Organization

### 5.1 Video Routes
**File**: `/backend/app/routes/video.py`

```
POST   /api/videos/upload              - Upload video file
POST   /api/videos/upload-url          - Upload from video URL (with yt-dlp)
GET    /api/videos/<id>/status         - Check processing progress
GET    /api/videos/<id>                - Get video metadata
GET    /api/videos/<id>/preview        - Download preview image
GET    /api/videos/list                - List all uploaded videos
POST   /api/videos/<id>/process        - Trigger video processing
GET    /api/videos/<id>/stream         - Stream video playback
GET    /api/videos/<id>/subtitle       - Get SRT subtitles
POST   /api/videos/<id>/generate-summary - Generate content summary
POST   /api/videos/<id>/generate-tags  - Generate topic tags
DELETE /api/videos/<id>                - Delete video and related data
GET    /api/videos/status/<task_id>    - Check Celery task status
```

**Key Features**:
- Max upload: 500MB
- Supported formats: mp4, avi, mov, mkv, webm
- MD5 deduplication to prevent duplicate uploads
- URL uploads via yt-dlp (YouTube, Bilibili, etc.)

### 5.2 Subtitle Routes
**File**: `/backend/app/routes/subtitle.py`

```
GET    /api/subtitles/video/<video_id>     - Get subtitles for video
GET    /api/subtitles/<subtitle_id>        - Get single subtitle
POST   /api/subtitles/upload               - Manual subtitle upload
PUT    /api/subtitles/<subtitle_id>        - Edit subtitle
DELETE /api/subtitles/<subtitle_id>        - Delete subtitle
GET    /api/subtitles/export/<video_id>    - Export as SRT/VTT
```

### 5.3 QA Routes
**File**: `/backend/app/routes/qa.py`

```
POST   /api/qa/ask                   - Ask question (video-specific or free)
GET    /api/qa/history/<video_id>    - Get QA history for video
```

**Request Body**:
```json
{
  "video_id": 1,
  "question": "What is the main topic?",
  "mode": "video",           // "video" or "free"
  "stream": true,            // Stream response?
  "use_ollama": false,       // Local or cloud LLM?
  "deep_thinking": false,    // Enable reasoning chain?
  "api_key": "sk-..."        // For cloud APIs
}
```

### 5.4 Knowledge Graph Routes
**File**: `/backend/app/routes/knowledge_graph.py`

```
GET    /api/knowledge-graph/<video_id>      - Get graph nodes and edges
GET    /api/knowledge-graph/<video_id>/concepts - Get extracted concepts
POST   /api/knowledge-graph/merge            - Combine multiple video graphs
GET    /api/knowledge-graph/<video_id>/search - Search graph by keyword
```

### 5.5 Knowledge Graph Integration Routes
**File**: `/backend/app/routes/knowledge_graph_integration.py`

```
POST   /api/knowledge-graph-integration/build - Build graph from subtitles
POST   /api/knowledge-graph-integration/update - Update existing graph
GET    /api/knowledge-graph-integration/status - Check build progress
```

### 5.6 Note Routes
**File**: `/backend/app/routes/note.py`

```
POST   /api/notes                     - Create note
GET    /api/notes/<note_id>           - Get note
PUT    /api/notes/<note_id>           - Update note
DELETE /api/notes/<note_id>           - Delete note
GET    /api/notes/video/<video_id>    - Get notes for video
POST   /api/notes/<note_id>/link      - Link to video timestamp
```

### 5.7 Chat Routes
**File**: `/backend/app/routes/chat.py`

```
POST   /api/chat/send              - Send chat message
GET    /api/chat/history           - Get chat history
```

### 5.8 Authentication Routes
**File**: `/backend/app/routes/auth.py`

```
POST   /api/auth/register          - User registration
POST   /api/auth/login             - User login (JWT)
POST   /api/auth/logout            - User logout
POST   /api/auth/refresh           - Refresh JWT token
GET    /api/auth/profile           - Get user profile
PUT    /api/auth/profile           - Update profile
```

---

## 6. Major Workflows

### 6.1 Video Upload & Processing Workflow

```
User Upload
    ↓
POST /api/videos/upload
    ├─ File validation (extension, size)
    ├─ Save to disk: /backend/uploads/
    ├─ Calculate MD5 hash
    ├─ Create Video record (status=UPLOADED)
    ├─ Commit to database
    └─ Return video_id
         ↓
User Triggers Processing (Auto or Manual)
    ├─ POST /api/videos/{id}/process
    └─ Celery task: process_video(video_id, language, model)
         ├─ Generate preview image
         ├─ Extract audio (FFmpeg)
         ├─ Transcribe audio (Whisper)
         ├─ Format subtitles (SRT)
         ├─ Generate summary (Ollama/API)
         ├─ Extract tags (LLM)
         ├─ Update Video.status = COMPLETED
         └─ User can view results
              ├─ Get subtitles: GET /api/videos/{id}/subtitle
              ├─ Get summary: Video.summary field
              ├─ Get tags: Video.tags field
              └─ View preview: GET /api/videos/{id}/preview
```

### 6.2 Knowledge Graph Construction Workflow

```
Video Successfully Processed
    ├─ Subtitles available
    └─ POST /api/knowledge-graph-integration/build
         ├─ Parse subtitles into segments
         ├─ Extract key concepts via LLM
         ├─ Extract entities and relationships
         ├─ Create Neo4j nodes:
         │  ├─ Concept nodes
         │  ├─ Entity nodes
         │  ├─ Time segment nodes
         │  └─ Learning objective nodes
         ├─ Create relationships:
         │  ├─ concept_IN_segment
         │  ├─ entity_APPEARS_IN_concept
         │  ├─ prerequisite_FOR
         │  └─ related_TO
         └─ Return graph structure
              └─ GET /api/knowledge-graph/{id}
                 ├─ Nodes with properties
                 ├─ Edges with relationships
                 └─ Graph visualization data
```

### 6.3 Question Answering Workflow

```
User Question
    └─ POST /api/qa/ask
         ├─ Validate video exists (if video mode)
         ├─ Create Question record
         ├─ QASystem.create_knowledge_base() from subtitles
         │  ├─ Parse subtitle file
         │  ├─ Chunk text semantically
         │  ├─ Generate embeddings
         │  └─ Build vector index
         │
         ├─ QASystem.get_answer_stream(question)
         │  ├─ Retrieve relevant subtitle chunks (RAG)
         │  ├─ Build prompt with context
         │  ├─ Stream response from LLM
         │  │  ├─ Ollama (local)
         │  │  └─ OpenAI/Qwen (cloud)
         │  └─ Yield response chunks
         │
         ├─ Update Question.answer
         └─ User receives streamed response
```

### 6.4 Note Creation & Linking Workflow

```
User Creates Note
    └─ POST /api/notes
         ├─ Create Note record
         ├─ Optionally link to video_id
         └─ Generate embeddings (content_vector)

User Links Note to Video Timestamp
    └─ POST /api/notes/{id}/link
         ├─ Create NoteTimestamp record
         ├─ time_seconds: video position
         ├─ subtitle_text: matching subtitle
         └─ Enable time-based note retrieval

User Views Notes for Video
    └─ GET /api/notes/video/{video_id}
         ├─ Query notes by video_id
         ├─ Include timestamps for each note
         └─ Display with timeline synchronization
```

---

## 7. Technology Stack

### Backend Framework
- **Flask** 2.x - Web framework
- **Flask-SQLAlchemy** - ORM layer
- **Flask-Migrate** - Database versioning
- **Flask-CORS** - Cross-origin support

### Async Processing
- **Celery** - Distributed task queue
- **Redis** - Message broker & result backend

### Database
- **MySQL** - Relational data (videos, users, notes, QA)
- **Neo4j** - Knowledge graph storage

### AI/ML Components
- **OpenAI Whisper** - Speech-to-text transcription
- **Ollama** - Local LLM inference (deepseek-r1:8b)
- **LangChain** - RAG framework
- **Qwen/OpenAI API** - Cloud LLM inference

### Video Processing
- **OpenCV** - Video frame extraction, preview generation
- **FFmpeg** - Audio extraction, video codec conversion
- **yt-dlp** - YouTube/video URL downloading

### Utilities
- **pydub** - Audio manipulation
- **torch** - GPU acceleration (CUDA/MPS)
- **python-dotenv** - Environment configuration

---

## 8. Configuration & Deployment

### 8.1 Environment Configuration
**File**: `/backend/config.py`

```python
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5001
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/ai_edvision'
NEO4J_URI = 'bolt://localhost:7687'
QWEN_API_KEY = '...'
WHISPER_MODEL = 'base'  # tiny, base, small, medium, large
REDIS_URL = 'redis://localhost:6379/0'
```

### 8.2 Required Services
```
Docker/Local Services Required:
├─ MySQL (port 3306) - Primary database
├─ Redis (port 6379) - Celery broker
├─ Neo4j (port 7687) - Knowledge graph database
├─ Ollama (port 11434) - Local LLM server (optional)
└─ Celery Worker (default) - Task processing
```

### 8.3 Startup Commands

```bash
# Terminal 1: Flask API server
python run.py

# Terminal 2: Celery worker (solo pool for Mac, prefork for Linux)
celery -A celery_app worker --loglevel=info

# Terminal 3: Ollama (if using local LLM)
ollama serve

# Frontend (separate project)
npm run dev  # at http://localhost:328
```

---

## 9. Key Design Patterns

### 9.1 Application Factory Pattern
Centralized app creation for testing and flexibility:
```python
app = create_app(config_name='development')
```

### 9.2 Task-Based Processing
Heavy operations delegated to Celery:
- Video processing (transcription, preview generation)
- Graph construction
- Content analysis

### 9.3 Layered Architecture
```
Routes (API Layer)
    ↓
Services (Business Logic)
    ├─ summary_generator.py
    ├─ tag_generator.py
    ├─ llm_similarity_service.py
    └─ qa_utils.py
    ↓
Models (Data Layer)
    ├─ Video, Subtitle, Note
    ├─ Question, User
    └─ Database relationships
    ↓
Tasks (Async Layer - Celery)
    ├─ video_processing.py
    ├─ audio_processing.py
    └─ subtitle_tasks.py
    ↓
Extensions (Infrastructure)
    ├─ db (SQLAlchemy)
    ├─ celery (Celery)
    └─ migrate (Alembic)
```

### 9.4 Platform-Specific Optimization
Different code paths for Mac (MPS GPU) vs Linux/Windows (CUDA):
- `video_processing.py` - Standard version
- `video_processing_mac.py` - Mac MPS optimization
- `rag_system.py` vs `rag_system_mac.py`

---

## 10. Data Flow Diagram

```
Frontend (Vite/React)
    │
    ├─→ POST /api/videos/upload ──→ Upload & Store File
    │                                      │
    │                                      ↓
    │                          Video Model (UPLOADED)
    │                                      │
    │   POST /api/videos/{id}/process ←───┘
    │                                      │
    │                                      ↓
    │                        Celery Task Queue (Redis)
    │                                      │
    │   ┌──────────────────────────────────┼──────────────────────────┐
    │   │                                   │                           │
    │   ↓                                   ↓                           ↓
    │ FFmpeg (extract audio)          Whisper (transcribe)        OpenCV (preview)
    │   │                                   │                           │
    │   └──────────────────────────────────┼──────────────────────────┘
    │                                       │
    │                                       ↓
    │                    MySQL: Video, Subtitle records
    │                                       │
    │   GET /api/videos/{id}/subtitle ←────┤
    │                                       │
    │                                       ↓
    │                    LLM Services (Summary, Tags)
    │                                       │
    │                                       ↓
    │               Neo4j: Knowledge Graph construction
    │                                       │
    │   GET /api/knowledge-graph/{id} ←────┤
    │                                       │
    │   POST /api/qa/ask (with RAG) ←──────┤
    │       │                               │
    │       ├─→ LangChain RAG ──→ LLM ──→ Streamed Response
    │       │
    │       ↓
    └──────→ User Interface Display
```

---

## 11. Performance Considerations

### 11.1 Async Processing
- Long-running tasks (transcription, graph building) are offloaded to Celery
- Users get immediate response with task_id for polling
- Progress updates available via `/api/videos/{id}/status`

### 11.2 GPU Acceleration
- CUDA support for NVIDIA GPUs (Whisper, embeddings)
- MPS support for Apple Silicon Macs (specialized worker)
- CPU fallback with optimization flags

### 11.3 Caching & Optimization
- Embeddings cached in NoteTimestamp model
- Knowledge graphs indexed in Neo4j
- Subtitle chunks pre-computed for RAG

### 11.4 Resource Management
- Celery solo pool (Mac) vs prefork (Linux/Windows)
- Worker max tasks per child: 5 (prevent memory leaks)
- Task timeout: 3 hours (accommodates large models)
- GPU cache clearing after transcription

---

## 12. Error Handling & Resilience

### 12.1 Video Processing Failures
- Placeholder file detection (text files masquerading as videos)
- Graceful handling of unsupported formats
- Detailed error messages in `Video.error_message`
- Automatic status update to FAILED with rollback

### 12.2 Celery Task Resilience
- Task acks_late: True (acknowledge after completion)
- Task reject_on_worker_lost: True (requeue if worker dies)
- Max retries: 2 (prevent infinite loops)
- Soft timeout: 2.9 hours (graceful shutdown before hard timeout)

### 12.3 Database Consistency
- Transaction rollback on error
- Foreign key constraints enforced
- Cascading deletes for cleanup (notes, subtitles)

---

## 13. File Structure Summary

```
backend/
├── app/
│   ├── __init__.py                 ← Flask app factory
│   ├── extensions.py               ← DB, Celery, CORS
│   ├── config.py                   ← Configuration
│   │
│   ├── models/
│   │   ├── video.py               ← Video + VideoStatus enum
│   │   ├── subtitle.py            ← Subtitle segments
│   │   ├── note.py                ← Notes + NoteTimestamp
│   │   ├── qa.py                  ← Questions
│   │   └── user.py                ← User accounts
│   │
│   ├── routes/
│   │   ├── video.py               ← Video APIs (upload, process)
│   │   ├── subtitle.py            ← Subtitle APIs
│   │   ├── qa.py                  ← QA APIs
│   │   ├── knowledge_graph.py      ← Graph queries
│   │   ├── knowledge_graph_integration.py ← Graph building
│   │   ├── note.py                ← Note APIs
│   │   ├── chat.py                ← Chat APIs
│   │   ├── auth.py                ← Authentication
│   │   └── __init__.py            ← Blueprint registration
│   │
│   ├── tasks/
│   │   ├── video_processing.py     ← Main transcription pipeline
│   │   ├── video_processing_mac.py ← Mac MPS optimization
│   │   ├── audio_processing.py     ← Audio extraction
│   │   ├── subtitle_tasks.py       ← Subtitle formatting
│   │   └── test.py                ← Test tasks
│   │
│   └── utils/
│       ├── knowledge_graph_utils.py ← Neo4j management
│       ├── qa_utils.py             ← RAG system
│       ├── rag_system.py / rag_system_mac.py
│       ├── semantic_utils.py       ← Embeddings
│       └── [other utilities]
│
├── services/
│   ├── summary_generator.py        ← Summary via LLM
│   ├── tag_generator.py            ← Tag extraction
│   ├── llm_similarity_service.py   ← Semantic similarity
│   └── similarity_service.py       ← Backup similarity
│
├── celery_app.py                   ← Celery entry point
├── config.py                       ← Config class
├── run.py                          ← Flask server entry
├── requirements.txt                ← Python dependencies
├── Dockerfile                      ← Docker image
└── migrations/                     ← Database migrations
```

---

## 14. Future Enhancement Opportunities

1. **Caching Layer**: Redis caching for frequently accessed videos/graphs
2. **Search Index**: Elasticsearch for full-text subtitle search
3. **Real-time Collaboration**: WebSocket support for simultaneous note editing
4. **Advanced Analytics**: LLM-based learning path recommendations
5. **Multi-language Support**: Support for more languages beyond zh/en
6. **Video Compression**: Automated video codec optimization
7. **Distributed Processing**: Multi-server Celery setup for horizontal scaling
8. **Graph Database Optimization**: Better indexing strategies for large graphs
