# 2026-04-22 System Requirements & Operations Summary

## Scope

- Local frontend: `mobile-frontend/`
- Cloud backend runtime directory: `/var/www/edumind-backend`
- Service: `edumind-api.service`
- Maintenance timer: `edumind-maintenance.timer`

## Branch Naming

- Applied branch pattern (English for `0422-功能/所做操作总结`):
  - `0422-system-hardening/operation-summary`

## 7-Requirement Verification (Backend)

Validation command:

```bash
cd /Users/yuan/final-work/edumind-backend
python3 scripts/validate_system_requirements.py
```

Validation result:

- `all_ok: true`
- effective: pass
- efficient: pass
- safe: pass
- robust: pass
- monitorable: pass
- updatable: pass
- compounding: pass

Additional hardening delivered:

- Added governance bypass guard so learning-flow tools reject direct invocation outside gateway.
- Added compatibility telemetry facade at `app/services/analytics/` while keeping canonical implementation in `app/analytics/`.

## Runtime Verification (Server)

- `edumind-api.service`: `active`
- `edumind-maintenance.timer`: `active`
- Health endpoint: `http://127.0.0.1:2004/health` returns `healthy`
- Process confirms backend split runtime:
  - `/var/www/edumind/.venv/bin/python /var/www/edumind-backend/run_prod.py`

## Functional Checks (Local Frontend + Cloud Backend)

- Video upload and processing: passed end-to-end (`pending -> processing -> completed`).
- Keyword search: passed with positive hits on processed content.
- Local dev proxy (`localhost:5173` -> cloud backend): passed for login/upload/status/search.

## Notes

- Current server backend remote is set to:
  - `https://github.com/yjy-yjy-yuan/edumind-backend`
- Server disk usage is high and should be watched:
  - `/dev/vda3` around `93%` used at validation time.
