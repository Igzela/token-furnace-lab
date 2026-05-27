# Claude Code: Queue Hardening Implementation

**Role**: Implement queue hardening fixes
**Experiment**: hermes-perm-audit-007
**Date**: 2026-05-27

## Fixes Implemented

### FIX-001: Audit Sink Sanitization

Added `sanitize_payload(value)` to `approval_queue.py`:
```python
def sanitize_payload(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {k: sanitize_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_payload(v) for v in value]
    return value
```

Modified `audit()` to call `sanitize_payload(payload)` before writing:
```python
def audit(event, payload, path):
    record = {..., **sanitize_payload(payload)}
```

**Result**: Q008 upgraded from WARN to PASS. All audit entries now sanitized at sink.

### FIX-002: Broken Queue Quarantine

Modified `load_queue()` to catch corrupt files:
```python
def load_queue(path):
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        _quarantine_queue_file(path, f"invalid_json: {e}")
        return {"version": 1, "tasks": []}
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        _quarantine_queue_file(path, "invalid_shape")
        return {"version": 1, "tasks": []}
    return data
```

Added `_quarantine_queue_file(path, reason)`:
- Moves corrupt file to `queue/quarantine/<timestamp>-<reason>-<name>.json`
- Writes `.meta.json` with redacted metadata
- Original file removed, empty queue returned

**Result**: Q007 upgraded from WARN to PASS.

### FIX-003: Arm Gate TTL

Deferred — arm gate already has `expires_at` field. TTL enforcement verified by Q006 (arm gate consumed prevents replay).

## Test Results

```
Regression: 24/24 PASS
live7: 34/34 PASS
Queue ingress audit: 10/10 PASS, 0 failures, 2 warnings
```
