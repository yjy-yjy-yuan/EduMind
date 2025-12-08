# Tests Overview

This folder holds automated checks for the backend. No code here—only a map of what each suite covers.

- `api/`: Endpoint-level tests for auth, chat, knowledge graph, notes, QA, subtitles, and videos—validate HTTP responses and payload shapes.
- `integration/`: Cross-service workflows (e.g., video + subtitle pipeline, QA workflow, Celery task interactions) to ensure components cooperate end to end.
- `smoke/`: Fast sanity checks (app can start/respond) to catch obvious breakage early.
- `unit/`: Fine-grained tests for models, services, tasks, and utilities in isolation.
- `conftest.py`: Shared fixtures/test config reused across the suites.
