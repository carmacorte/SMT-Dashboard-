# SMTinel Live Integration

This package includes a non-breaking SMTinel Live adapter.

## Files added

- `frontend/index_traceops_live.html`: original SMTinel HTML with inline Live Mode adapter.
- `export/smtinel_adapter.js`: standalone copy of the same adapter for future modular loading.

## Behavior

The adapter adds a Source Mode dock:

- `ZIP Upload`: keeps the existing manual import workflow.
- `Live WhatsApp MCP`: connects to TraceOps Live API and auto-refreshes KPIs, incidents and Sentinel alerts.

Default API base URL:

```text
http://127.0.0.1:8000
```

This can be changed from the API button in the SMTinel dock. The value is persisted in `localStorage` as `traceops_live_api_base`.

## Startup

From the TraceOps Live folder:

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
frontend/index_traceops_live.html
```

Switch to `Live WhatsApp MCP`, then press `Refresh`.

## Validation performed

```bash
python -m compileall -q .
python -m pytest -q
node -c export/smtinel_adapter.js
```

Result: 17 tests passed. Pydantic v2 deprecation warnings remain but do not block execution.
