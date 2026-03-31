# Repository Guidelines

## Project Positioning
This repository is now an iOS-only mobile learning project for MacBook Pro development. The only supported product chain is:

1. `mobile-frontend/` as the frontend UI layer
2. `backend_fastapi/` as the real backend capability layer
3. `ios-app/` as the iOS `WKWebView` container and native execution layer for on-device features

Do not reintroduce `frontend/`, `backend/`, Android modules, or desktop-web-specific product branches.

## Project Structure & Module Organization
- `backend_fastapi/`: the only backend service. All server-side business logic, database access, upload handling, audio extraction, transcription, analysis, notes, QA, and graph features belong here.
- `mobile-frontend/`: the only frontend codebase. It provides the H5 UI loaded by iOS `WKWebView`.
- `ios-app/`: the iOS container project, native bridge layer, on-device media/file access, on-device audio extraction/transcription execution, and Web asset sync script.
- `docs/`: only keep documents that directly support the iOS mobile chain, Mac development, backend deployment, database setup, or video-processing workflow.
- `CHANGELOG.md`, `README.md`, `PROJECT_MOBILE_IMPLEMENTATION_PROMPT.md`: root-level control documents that must stay aligned with the current iOS-only architecture.

## Architecture Rules
- UI is frontend, real functionality is backend.
- `mobile-frontend/` must not implement database logic, model inference, or fake “real processing” in page code.
- `backend_fastapi/` remains the default online execution layer for uploads, FFmpeg extraction, Whisper transcription, database writes, summaries, QA, and similar features.
- `ios-app/` is the only on-device execution layer for iOS-native capabilities such as local file picking, media access, audio extraction, local task persistence, and on-device transcription.
- Frontend and backend communicate through HTTP ports and documented APIs; frontend and `ios-app/` communicate through a documented `WKWebView` bridge.
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

iOS native validation:

```bash
bash ios-app/validate_ios_build.sh
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
- For `ios-app/` native changes, at minimum run an iOS build validation and verify the affected bridge or native flow in the container.

## Commit & Pull Request Guidelines
- Use short imperative commit titles.
- Keep each commit focused on one change.
- Before any commit, explicitly remind the user to review the current branch, staged files, test/verification status, and whether any secrets or machine-local settings are being included.
- Before any commit, explicitly remind the user that `git status`, `git diff --staged`, and `git log --oneline -5` are the minimum review commands if they have not already checked them.
- PRs should state:
  - affected module
  - verification steps
  - screenshots for `mobile-frontend/` or iOS UI changes
  - whether `ios-app/EduMindIOS/EduMindIOS/WebAssets/` was refreshed

变更日志规范：

- 所有变更只在 `CHANGELOG.md` 中追加新条目，不修改或删除历史记录。
- 如果需要更正历史说明，在最新条目中写“对某某日期记录的更正说明”。

## Git Hooks Guidance
When a task involves Git hooks, first thoroughly analyze the current project to determine:

1. **Existing Git hooks setup**:
   - Check for any existing Git hooks configuration:
     - `.husky/` directory
     - `.git/hooks/` (sample files or custom scripts)
     - `.pre-commit-config.yaml` (pre-commit framework)
     - `lefthook.yml`, simple-git-hooks config, or other tools
     - Any `prepare` script or `gitHooks` in `package.json`
   - If hooks exist, examine their content:
     - What hooks are implemented (`pre-commit`, `pre-push`, `commit-msg`, etc.)?
     - What commands do they run?
     - Do they follow best practices (run only on staged files, fast, cached, CI-compatible, skippable)?
     - Are they reasonably complete and effective?

2. **Project characteristics**:
   - Primary programming language(s)
   - Key build/config files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.)
   - Whether it's a monorepo
   - Existing linters/formatters/tests
   - Test framework in use

**Decision logic for hooks**:
- If existing hooks are **reasonable and complete** (cover pre-commit fast checks, pre-push tests, commit-msg linting, follow best practices, fast, CI-compatible):
  - Optimize only if clear improvements are possible (for example, add caching, better ignore patterns, secrets check).
  - Otherwise, leave them untouched and only add truly missing critical parts.
- If existing hooks are **partially reasonable but incomplete/outdated**:
  - Extend/improve the existing toolchain (do not replace unless necessary).
- If existing hooks are **missing, broken, or significantly suboptimal**:
  - Replace or set up a new appropriate toolchain.
- If no hooks exist at all:
  - Set up a fresh toolchain based on project type.

**Toolchain selection** (only if setting up new or replacing):
- JS/TS projects with `package.json` -> prefer Husky (v8+) + lint-staged + commitlint
- Python, Go, Rust, Ruby, multi-language, or monorepos -> prefer cross-language pre-commit framework
- Respect any existing toolchain and extend it when possible.

Set up or improve Git hooks following industry best practices.

### Requirements (apply to new or improved hooks)
1. **Pre-commit** (fast, staged files only):
   - Lint + format with project-appropriate tools
   - Type checking if applicable
   - Optional: block `console.log`/`debugger`, check for secrets
2. **Pre-push**:
   - Run tests + type checking
   - Optional: integration tests / build
3. **Commit-msg**:
   - Enforce conventional commits (`type(scope): description`)
   - Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

### Best Practices (enforce in all cases)
- Hooks must be fast (<10s typical pre-commit)
- Use caching where possible
- Skip automatically in CI
- Document `--no-verify` escape hatch
- Proper ignore patterns
- Clear setup instructions in `README.md`

### Implementation Steps (respect existing setup)
**If extending/improving Husky + lint-staged**:
- Keep existing `.husky` files, only modify if needed
- Update `lint-staged` config for better patterns/caching
- Ensure `"prepare": "husky install"`

**If extending/improving pre-commit framework**:
- Keep/modify existing `.pre-commit-config.yaml`
- Add missing hooks (formatting, linting, tests, commitlint)

**If setting up fresh**:
- Husky route: install dependencies, create `.husky/*`, add `prepare` script
- pre-commit route: create `.pre-commit-config.yaml`, run `pre-commit install`

### Example configurations
[保持之前的 JS/TS lint-staged 示例、Python/Go/Rust pre-commit 示例不变]

### Final steps
- Update `README.md` with clear setup instructions and hook descriptions
- Commit all configuration files to version control
- Ensure new contributors can run one command to install hooks

## Configuration & Safety
- Do not commit real secrets from `.env` files or machine-local settings.
- The database must remain MySQL when implementing backend persistence.
- Do not change database tables casually.
- Prefer adapting to the existing schema and existing tables instead of adding new tables.
- If an API contract changes, update the related docs and prompts in the same patch.
- Do not clone external reference repositories into this project tree; if an external project is used as reference, absorb only the necessary implementation ideas into the existing modules.

## iOS WebView Validation Rules
- Every `mobile-frontend/` interaction change must be validated in the iOS `WKWebView` container, not only in a desktop browser.
- After frontend changes, rebuild `mobile-frontend` and sync the latest `dist/` into `ios-app/EduMindIOS/EduMindIOS/WebAssets/`.
- For tap or route-transition features, verify:
  - touch is reachable
  - route actually changes
  - target page renders correctly in iOS
- For `ios-app/` bridge or native execution changes, verify:
  - H5 can detect the native bridge
  - native message dispatch returns to the page
  - native-triggered UI state changes render correctly in `WKWebView`

## Removal Policy
- Files unrelated to the iOS mobile chain should not be restored.
- Do not add back legacy desktop-web modules, Flask compatibility branches, or Android app code unless explicitly requested.

## The use of pytest to test the modified program is prohibited.
