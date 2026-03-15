# Repository Guidelines

## Project Structure & Module Organization
`backend_fastapi/` is the primary backend and should receive new API work first. `backend/` is the legacy Flask service kept for compatibility. `frontend` contains the desktop Vue app, and `mobile-frontend/` contains the mobile H5/WebView app (for both browser and native shells such as iOS WebView). Shared backend tests live in `tests/`; FastAPI-specific tests also exist in `backend_fastapi/tests/`. Keep docs and prompt files in `docs/` and the repository root.

## Build, Test, and Development Commands
Backend setup: `pip install -r backend_fastapi/requirements.txt` or `pip install -e .[dev,test]`. Run FastAPI locally with `python backend_fastapi/run.py`. Run the desktop app with `cd frontend && npm install && npm run dev`. Run the mobile web app with `cd mobile-frontend && npm install && npm run dev`. Run the main automated suite from the repo root with `pytest`.

## Coding Style & Naming Conventions
Python follows Black and isort settings from `pyproject.toml`: 4-space indentation, 120-character lines, and explicit imports. Vue and JavaScript should keep existing Vite structure, use descriptive file names such as `VideoDetail.vue` and `test_video_api.py`, and avoid mixing API logic into view files. Prefer small top-level helpers over deeply scoped closures; do not introduce nested functions unless there is a hard technical reason.

## Testing Guidelines
Pytest is the default framework. Place tests under `tests/unit/`, `tests/api/`, `tests/integration/`, or `tests/smoke/` based on scope, and name files `test_*.py`. Use markers defined in `pytest.ini` such as `pytest -m smoke` for quick checks. The configured coverage floor is currently low (`fail_under = 25`), but new features should include direct unit or API coverage.

## Commit & Pull Request Guidelines
Recent history uses short imperative subjects, often with `chore:` prefixes or concise Chinese summaries. Keep commit titles focused on one change, for example `chore: rename mobile android shell` or `更新移动端提示词文档`. PRs should describe the affected module, list verification steps, link related issues, and include screenshots for `frontend/` 或 `mobile-frontend/` 的 UI 改动。

变更日志规范：

- 所有变更只在 `CHANGELOG.md` 中**追加新条目**，不要修改或删除历史记录。
- 如果需要更正历史说明，请在最新一条记录中写明“对某某日期记录的更正说明”，保持时间线清晰可追溯。

## Configuration & Safety
Do not commit real secrets from `.env` files or machine-local platform settings. When changing API contracts, update the related docs and prompt files in the same patch so mobile and backend work stay aligned.

## iOS WebView Validation Rules
- For `mobile-frontend/` interaction changes, validation must include iOS container behavior (WKWebView), not only desktop browser build output.
- After frontend changes, rebuild `mobile-frontend` and ensure latest `dist/` is copied into iOS app Web assets before claiming the fix is complete.
- For tap/click features, verify route transition and target page rendering in iOS runtime logs and UI (for example `/videos?scope=...` from home stat cards).
