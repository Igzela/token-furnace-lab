# GPT: Hardening Architecture Review

**Role**: Review queue hardening architecture
**Experiment**: hermes-perm-audit-007
**Date**: 2026-05-27

## Fix Assessment

### FIX-001: Audit Sink Sanitization

**Approach**: `sanitize_payload()` recursively applies `sanitize_text()` to all strings in the payload before writing.

**Assessment**: Correct. Defense-in-depth — caller sanitize + sink sanitize. The recursive approach handles nested dicts and lists. Non-string values pass through unchanged (int, bool, None).

**Edge cases**:
- Very large payloads: `sanitize_text` truncates to 500 chars per string, so nested payloads are bounded
- Non-string keys: not sanitized (keys are typically short identifiers, not user input)
- Callable values: not expected in audit payloads

### FIX-002: Broken Queue Quarantine

**Approach**: `load_queue()` catches corrupt JSON and invalid shape, quarantines the file, returns empty queue.

**Assessment**: Correct. The quarantine directory structure is good:
- `queue/quarantine/<timestamp>-<reason>-<name>.json` — the corrupt file
- `queue/quarantine/<timestamp>-<reason>-<name>.meta.json` — redacted metadata

**Key property**: quarantined files are NOT replayable (meta.replayable = false). Recovery requires creating a new task, not moving the file back.

### FIX-003: Arm Gate TTL

**Status**: Deferred. Arm gate already has `expires_at` field. Q006 verifies consumption prevents replay.

**Assessment**: Correct deferral. The arm gate TTL is already implemented at the worker level. No additional code needed.

## Verdict

Both implemented fixes are correct and minimal. No over-engineering. The recursive sanitize_payload is the right approach for sink sanitization. The quarantine mechanism is simple and effective.
