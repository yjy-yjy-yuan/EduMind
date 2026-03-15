# Repository Guidelines

## Project Positioning
This repository is now an iOS-only mobile learning project for MacBook Pro development. The only supported product chain is:

1. `mobile-frontend/` as the frontend UI layer
2. `backend_fastapi/` as the real backend capability layer
3. `ios-app/` as the iOS `WKWebView` container

Do not reintroduce `frontend/`, `backend/`, Android modules, or desktop-web-specific product branches.

## Project Structure & Module Organization
- `backend_fastapi/`: the only backend service. All real business logic, database access, upload handling, audio extraction, transcription, analysis, notes, QA, and graph features belong here.
- `mobile-frontend/`: the only frontend codebase. It provides the H5 UI loaded by iOS `WKWebView`.
- `ios-app/`: the iOS container project and Web asset sync script.
- `docs/`: only keep documents that directly support the iOS mobile chain, Mac development, backend deployment, database setup, or video-processing workflow.
- `CHANGELOG.md`, `README.md`, `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`: root-level control documents that must stay aligned with the current iOS-only architecture.

## Architecture Rules
- UI is frontend, real functionality is backend.
- `mobile-frontend/` must not implement business rules, direct database logic, or fake “real processing” in page code.
- `backend_fastapi/` is the only execution layer for uploads, FFmpeg extraction, Whisper transcription, database writes, summaries, QA, and similar features.
- Frontend and backend communicate only through HTTP ports and documented APIs.
- The default backend entry is `/Users/yuan/final-work/EduMind/backend_fastapi`.
- The product target is iOS, not a standalone desktop website.

## Build, Test, and Development Commands
Always use a virtual environment before Python dependency installation or backend startup.

Backend:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend_fastapi/requirements.txt
python backend_fastapi/run.py
```

Mobile frontend:

```bash
cd mobile-frontend
npm install
npm run dev
npm run build:ios
```

iOS Web assets sync:

```bash
bash ios-app/sync_ios_web_assets.sh
```

FastAPI tests:

```bash
. .venv/bin/activate
pytest backend_fastapi/tests/ -v
```

## Coding Style & Naming Conventions
- Python follows Black and isort settings from `pyproject.toml`: 4-space indentation, 120-character lines, explicit imports.
- Vue files should remain focused on UI state and API calls. Do not move backend logic into views.
- Use descriptive names such as `VideoDetail.vue`, `test_video_api.py`, `video_processing.py`.
- Prefer small top-level helpers over nested functions unless there is a hard technical reason.

## Testing Guidelines
- Pytest is the default Python test framework.
- Put backend tests in `backend_fastapi/tests/`.
- New backend features should include direct unit or API coverage.
- For frontend changes, build output alone is insufficient. iOS container validation is required.

## Commit & Pull Request Guidelines
- Use short imperative commit titles.
- Keep each commit focused on one change.
- PRs should state:
  - affected module
  - verification steps
  - screenshots for `mobile-frontend/` or iOS UI changes
  - whether `ios-app/EduMindIOS/EduMindIOS/WebAssets/` was refreshed

变更日志规范：

- 所有变更只在 `CHANGELOG.md` 中追加新条目，不修改或删除历史记录。
- 如果需要更正历史说明，在最新条目中写“对某某日期记录的更正说明”。

## Configuration & Safety
- Do not commit real secrets from `.env` files or machine-local settings.
- The database must remain MySQL when implementing backend persistence.
- Do not change database tables casually.
- Prefer adapting to the existing schema and existing tables instead of adding new tables.
- If an API contract changes, update the related docs and prompts in the same patch.

## iOS WebView Validation Rules
- Every `mobile-frontend/` interaction change must be validated in the iOS `WKWebView` container, not only in a desktop browser.
- After frontend changes, rebuild `mobile-frontend` and sync the latest `dist/` into `ios-app/EduMindIOS/EduMindIOS/WebAssets/`.
- For tap or route-transition features, verify:
  - touch is reachable
  - route actually changes
  - target page renders correctly in iOS

## Removal Policy
- Files unrelated to the iOS mobile chain should not be restored.
- Do not add back legacy desktop-web modules, Flask compatibility branches, or Android app code unless explicitly requested.
