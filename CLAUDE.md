# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-EdVision is an intelligent educational video analysis system built with Flask (backend) and Vue 3 (frontend). It processes videos to extract subtitles, builds knowledge graphs, and provides AI-powered Q&A capabilities using local LLMs (Ollama) or cloud APIs.

## Common Development Commands

### Backend (Flask + Celery)

```bash
# Navigate to backend directory
cd backend

# Activate conda environment
conda activate ai-edvision

# Start Flask development server (requires VPN on first launch)
python run.py

# Start Celery worker for async tasks (required for video processing)
python -m celery -A app.celery_app worker --loglevel=info -P solo

# Database operations
python init_db.py          # Initialize database (first time only)
python run_migration.py    # Run migrations (after init_db.py)
python update_tables.py    # Update table structure without deleting data
```

### Frontend (Vue 3 + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Start with network access (for testing on other devices)
npm run dev --host

# Build for production
npm run build

# Run linter
npm run lint

# Run unit tests
npm run test:unit
```

### Required Services

These services must be running before starting the application:

```bash
# Redis (required for Celery)
# Mac:
brew services start redis
# Windows: redis-server

# Neo4j (required for knowledge graph)
# Mac:
brew services start neo4j
# Windows: Start via Neo4j Desktop
# Web interface: http://localhost:7474

# Ollama (required for local LLM inference)
# Download models:
ollama pull deepseek-r1:8b
ollama pull qwen3:8b
```

## High-Level Architecture

### Backend Structure

The Flask backend follows a blueprint-based architecture with async task processing:

**Core Components:**
- **`app/__init__.py`**: Application factory pattern initialization
- **`app/models/`**: SQLAlchemy models (Video, Subtitle, Note, Question, User)
- **`app/routes/`**: 7 API blueprints (videos, subtitles, notes, qa, auth, knowledge_graph, chat)
- **`app/tasks/`**: Celery async tasks for video processing
- **`app/services/`**: Business logic (summary generation, tag extraction)
- **`app/utils/`**: Helper modules (knowledge graph, video processing)

**Video Processing Pipeline (7 stages):**
1. Preview generation (OpenCV)
2. Metadata extraction (FFmpeg)
3. Audio extraction (WAV)
4. Transcription (Whisper with GPU/MPS acceleration)
5. Subtitle formatting (SRT/VTT)
6. Content analysis (LLM-based summary + tags)
7. Finalization

**Platform-Specific Configuration:**
- Mac uses MPS (Metal Performance Shaders) for PyTorch acceleration
- Linux/Windows use CUDA for GPU acceleration
- Task processing modules differ: `video_processing_mac.py` vs `video_processing.py`

### Frontend Structure

Vue 3 application with Composition API and modular architecture:

**Key Directories:**
- **`src/views/`**: Page-level components (11 routes)
- **`src/components/`**: Reusable UI components (Navigation, VideoPlayer, VideoQA)
- **`src/api/`**: API integration layer (video, qa, chat, note modules)
- **`src/store/`**: Vuex state management (global video state, auth)
- **`src/router/`**: Route definitions
- **`src/utils/`**: Axios request interceptors and utilities

**Main User Workflows:**
1. **Video Upload → Processing → Playback**: Upload local/URL video → Celery processes → Watch with subtitles
2. **Q&A System**: Video-based RAG or free Q&A with streaming responses
3. **Note Taking**: Rich text editor with video timestamp linking and similarity search
4. **Knowledge Graph**: D3.js visualization of video content relationships

## Critical Configuration Files

### Backend Configuration

**`backend/config.py`**: Centralized configuration
- Neo4j connection: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Redis: `broker_url` and `result_backend` (localhost:6379)
- Database: `SQLALCHEMY_DATABASE_URI` (MySQL default, SQLite fallback)
- LLM APIs: `QWEN_API_KEY`, `QWEN_API_BASE`
- File upload limits: 500MB max

**Additional Neo4j configuration in:**
- `backend/app/utils/knowledge_graph_utils.py:KnowledgeGraphManager.__init__()`
- `backend/app/routes/knowledge_graph.py` (instantiation)

**Environment variables (`.env` in backend directory):**
```python
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///app.db  # or MySQL connection string
```

### Frontend Configuration

**`frontend/src/config/index.js`**: API base URL configuration
- Default: `http://localhost:5001`
- Override with `VITE_API_BASE_URL` environment variable

## Database Models and Relationships

**Video** (Core entity)
- Processing status: `pending`, `processing`, `completed`, `failed`
- Generated fields: `summary`, `tags`, `merged_subtitle` (semantic merge)
- Has many: Subtitles, Notes, Questions

**Subtitle**
- Time-synchronized segments: `start_time`, `end_time`, `content`
- Linked to Video via `video_id`

**Note**
- User-created notes with semantic embeddings
- Optional video linking with timestamp references
- Tag-based organization

**Question**
- Video-specific or free-form Q&A records
- Stores question, answer, and context

## Key Technical Patterns

### Backend

**Async Task Processing:**
- All video processing goes through Celery
- Task status tracked in database: `processing_status`, `processing_task_id`
- Use `get_video_status(video_id)` endpoint to poll progress

**LLM Integration:**
- Dual mode: Local (Ollama) or Cloud (Qwen/OpenAI-compatible)
- Streaming responses via `stream=True` parameter
- Located in: `app/services/summary_generator.py`, `app/services/tag_generator.py`

**Knowledge Graph:**
- Neo4j Cypher queries in `app/utils/knowledge_graph_utils.py`
- RAG-based retrieval for Q&A system
- Node similarity calculated by LLM embeddings

### Frontend

**API Communication:**
- Centralized Axios instance: `src/utils/request.js`
- 10-minute timeout for long operations
- Automatic FormData detection (removes Content-Type header)
- Error handling with user-friendly messages

**Streaming Responses:**
- Native Fetch API with ReadableStream
- Used in: `src/api/chat.js:sendChatMessage()`, Q&A components
- Real-time callbacks: `onData`, `onError`, `onComplete`

**State Management:**
- Vuex for global video state
- localStorage for chat history (per video and free mode)
- Direct API calls in components (minimal Vuex usage)

## Testing and Debugging

### Backend Testing
```bash
# Test Celery connectivity
celery -A app.celery_app inspect ping

# Test Redis connectivity
redis-cli ping  # Should return PONG

# Test Neo4j connectivity
# Open http://localhost:7474 in browser

# Check video processing task status
# Use GET /api/videos/:id/status endpoint
```

### Frontend Testing
```bash
# Run unit tests
npm run test:unit

# Check for linting issues
npm run lint

# Preview production build
npm run build && npm run preview
```

### Common Issues

**Video processing fails:**
- Ensure Celery worker is running
- Check Redis connection
- Verify FFmpeg is installed: `ffmpeg -version`
- Check Whisper model download: `openai-whisper` package
- Mac users: Ensure MPS-compatible PyTorch version

**Knowledge graph errors:**
- Verify Neo4j is running and accessible
- Check credentials in `config.py` and `knowledge_graph_utils.py`
- Default password often needs changing on first Neo4j startup

**Frontend can't connect to backend:**
- Verify Flask is running on port 5001
- Check CORS configuration in `backend/config.py`
- Ensure `VITE_API_BASE_URL` matches backend host

## Platform-Specific Considerations

### macOS (M1/M2/M3/M4)
- Use `faiss-cpu` (not `faiss-gpu`) via conda
- PyTorch uses MPS acceleration automatically
- Video processing uses `video_processing_mac.py`
- Install dependencies: `brew install redis neo4j ffmpeg`

### Windows
- Use `faiss-gpu` with CUDA support
- Video processing uses `video_processing.py`
- Redis installation: Download from Microsoft Archive
- FFmpeg: Add to PATH manually

### Linux
- Similar to Windows (CUDA support)
- Use system package manager for Redis, FFmpeg

## Development Workflow

### Adding a New Feature

1. **Backend API:**
   - Create/modify model in `app/models/`
   - Add route in appropriate blueprint in `app/routes/`
   - Implement business logic in `app/services/` or `app/utils/`
   - Update database: Run `python update_tables.py` if schema changes

2. **Frontend Integration:**
   - Add API method to `src/api/` module
   - Create/update view component in `src/views/`
   - Add route in `src/router/index.js` if needed
   - Update Vuex store if global state needed

3. **Testing:**
   - Test backend endpoints with Postman or curl
   - Test frontend flow in browser
   - Check browser console and backend logs for errors

### Video Processing Customization

To modify the processing pipeline:
- Edit `backend/app/tasks/video_processing_mac.py` (Mac) or `video_processing.py` (Windows/Linux)
- Update the 7-stage pipeline functions
- Modify `process_video()` in `backend/app/routes/video.py` to add/remove steps

### LLM Model Switching

To change the LLM backend:
- **Ollama (local):** Modify model names in summary/tag generators
- **Cloud API:** Update `QWEN_API_KEY` and `QWEN_API_BASE` in `.env`
- Code locations: `app/services/summary_generator.py`, `app/services/tag_generator.py`

## Important Code Locations

**Video upload and processing:**
- `backend/app/routes/video.py:upload_local_video()` - Handle file uploads
- `backend/app/routes/video.py:process_video()` - Trigger async processing
- `backend/app/tasks/video_processing_mac.py:process_video_task()` - Main pipeline

**Q&A system:**
- `backend/app/routes/qa.py:ask_question()` - Handle questions
- `backend/app/utils/knowledge_graph_utils.py:search_related_content()` - RAG retrieval
- `frontend/src/views/VideoPlayer.vue` - Q&A UI (1368 lines)

**Knowledge graph:**
- `backend/app/utils/knowledge_graph_utils.py:KnowledgeGraphManager` - Neo4j operations
- `backend/app/routes/knowledge_graph.py` - Graph API endpoints
- `frontend/src/views/KnowledgeGraph.vue` - D3.js visualization

**Subtitle handling:**
- `backend/app/routes/subtitles.py` - CRUD operations
- `frontend/src/views/VideoPlayer.vue` - Display and sync with video

## Dependencies and Requirements

### Backend Key Dependencies
- **Python 3.10** (required version)
- Flask 3.0.2, Celery 5.4.0, Redis 5.0.1
- PyTorch 2.0.0 (with MPS or CUDA)
- openai-whisper 20240930
- neo4j 5.17.0
- sentence-transformers 3.4.1
- faiss-cpu/faiss-gpu 1.8.0
- See `backend/requirements.txt` for full list

### Frontend Key Dependencies
- Vue 3.3.4
- Element Plus 2.3.9 (UI components)
- Axios 1.4.0, Vue Router 4.2.4, Vuex 4.1.0
- D3.js 7.9.0 (knowledge graph visualization)
- WangEditor 5.1.23 (rich text editor)
- Socket.io-client 4.8.1
- See `frontend/package.json` for full list

### System Dependencies
- FFmpeg (video/audio processing)
- Ollama (local LLM inference)
- Redis (message broker)
- Neo4j (graph database)

## Code Style and Conventions

**Backend:**
- Follow PEP 8 Python style guide
- Use blueprints for route organization
- Async tasks for long-running operations
- SQLAlchemy models use camelCase for class names

**Frontend:**
- Vue 3 Composition API preferred
- Scoped styles in SFC components
- API layer separation from components
- ESLint with Vue plugin for linting

## Access URLs

**Development Environment:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5001
- Neo4j Browser: http://localhost:7474
- Redis: localhost:6379 (no web UI)

**Common API Endpoints:**
- `POST /api/videos/upload` - Upload video
- `GET /api/videos/:id/status` - Check processing status
- `POST /api/qa/ask` - Ask questions (with streaming)
- `GET /api/knowledge-graph/nodes` - Get graph nodes
- `POST /api/notes/notes` - Create note
