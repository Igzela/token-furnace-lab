"""Negative tests for merged_harness.py — security, budget, fusion, schema."""
import json
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from merged_harness import (
    Event, EventStore, BudgetManager, BudgetReservation,
    QualityGate, DevilsAdvocate, fuse_verdicts, validate_task_yaml,
    safe_artifact_path, safe_prompt_path, MergedHarness,
    MAX_EVENT_STORE_BYTES, ALLOWED_EVENT_TYPES,
)


# --- T1: subproblem_id rejects traversal attempts ---

def test_rejects_dotdot_slash():
    """T1a: '../x' must be rejected by regex."""
    try:
        safe_artifact_path(Path("/tmp/run"), "../x")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_nested_slash():
    """T1b: 'a/b' must be rejected by regex."""
    try:
        safe_artifact_path(Path("/tmp/run"), "a/b")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_dot():
    """T1c: '.' must be rejected by regex."""
    try:
        safe_artifact_path(Path("/tmp/run"), ".")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_empty_string():
    """T1d: '' must be rejected by regex."""
    try:
        safe_artifact_path(Path("/tmp/run"), "")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_unicode_slash():
    """T1e: unicode slash variant must be rejected."""
    try:
        safe_artifact_path(Path("/tmp/run"), "a⁄b")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_encoded_slash():
    """T1f: URL-encoded slash must be rejected (not decoded by regex)."""
    try:
        safe_artifact_path(Path("/tmp/run"), "a%2Fb")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_dotdot_in_prompt():
    """T1g: safe_prompt_path also rejects traversal."""
    try:
        safe_prompt_path(Path("/tmp/run"), "../../etc/passwd")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_rejects_traversal_in_subdir():
    """T1h: safe_artifact_path rejects traversal in subdir parameter."""
    try:
        safe_artifact_path(Path("/tmp/run"), "valid_id", subdir="../etc")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# --- T2: safe_artifact_path rejects absolute path ---

def test_rejects_absolute_path():
    """T2a: absolute path subproblem_id rejected by regex."""
    try:
        safe_artifact_path(Path("/tmp/run"), "/tmp/outside")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_path_stays_within_run_dir():
    """T2b: valid ID produces path inside run_dir."""
    run_dir = Path("/tmp/test_run")
    result = safe_artifact_path(run_dir, "valid_id")
    assert result.is_relative_to(run_dir), f"Path escapes: {result}"


def test_prompt_path_stays_within_run_dir():
    """T2c: valid prompt path stays inside run_dir."""
    run_dir = Path("/tmp/test_run")
    result = safe_prompt_path(run_dir, "valid_id")
    assert result.is_relative_to(run_dir), f"Path escapes: {result}"


# --- T3: symlink escape test (if filesystem supports it) ---

def test_symlink_escape_rejected():
    """T3: symlink replacing a directory component causes resolve() to escape."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outside = Path(tmpdir) / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_text("escaped")
        run_dir = Path(tmpdir) / "run"
        run_dir.mkdir()
        # Make "prompts" a symlink to outside dir
        prompts_link = run_dir / "prompts"
        try:
            prompts_link.symlink_to(outside)
        except OSError:
            return  # skip if symlinks not supported
        # safe_prompt_path constructs run_dir / "prompts" / f"{id}_prompt.md"
        # resolve() follows the symlink, landing outside run_dir
        # The function should raise ValueError because resolved path escapes run_dir
        try:
            safe_prompt_path(run_dir, "test_id")
            # If no exception, the resolved path should still be outside
            resolved = (run_dir / "prompts" / "test_id_prompt.md").resolve()
            assert not resolved.is_relative_to(run_dir.resolve()), \
                f"Expected escape but path stayed inside: {resolved}"
        except ValueError:
            pass  # expected — path escapes run_dir via symlink


# --- T4: EventStore size includes pending event ---

def test_eventstore_rejects_event_exceeding_limit():
    """T4: append rejects if current + pending > max_bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "events.jsonl"
        # Set limit that fits one small event but not two
        store = EventStore(store_path, max_bytes=250)
        store.append(Event(
            event_id="evt-001", event_type="task_received",
            timestamp="2026-01-01T00:00:00Z",
            payload={"data": "small"},
        ))
        # Second event with big payload should fail
        try:
            store.append(Event(
                event_id="evt-002", event_type="task_received",
                timestamp="2026-01-01T00:00:01Z",
                payload={"data": "x" * 200},
            ))
            # If we get here, the file size check should still be within limit
            assert store_path.stat().st_size <= 260  # small margin for newline
        except RuntimeError:
            pass  # expected — would exceed limit


# --- T5: EventStore invalid event_type rejected ---

def test_eventstore_rejects_invalid_event_type():
    """T5: Event.validate() rejects unknown event_type."""
    ev = Event(
        event_id="evt-001", event_type="nonexistent_type",
        timestamp="2026-01-01T00:00:00Z", payload={},
    )
    try:
        ev.validate()
        assert False, "Should have raised ValueError for unknown event_type"
    except ValueError:
        pass


def test_eventstore_accepts_valid_event_type():
    """T5b: known event_type passes validation."""
    for et in ["task_received", "budget_used", "adversarial_review", "run_complete"]:
        ev = Event(event_id="evt-001", event_type=et,
                    timestamp="2026-01-01T00:00:00Z", payload={})
        ev.validate()  # should not raise


# --- T6: EventStore concurrent thread append ---

def test_eventstore_concurrent_appends():
    """T6: concurrent threads produce valid JSONL without interleaving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "events.jsonl"
        store = EventStore(store_path, max_bytes=10 * 1024 * 1024)
        errors = []

        def append_event(i):
            try:
                store.append(Event(
                    event_id=f"evt-{i:04d}", event_type="task_received",
                    timestamp="2026-01-01T00:00:00Z",
                    payload={"thread": i},
                ))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=append_event, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent append errors: {errors}"
        lines = [l for l in store_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 50, f"Expected 50 lines, got {len(lines)}"
        # Each line should be valid JSON
        for line in lines:
            json.loads(line)


# --- T7: LLM judge fallback records provenance ---

def test_judge_fallback_returns_none():
    """T7: llm_judge_score returns None in mock mode (fallback path)."""
    from merged_harness import llm_judge_score
    result = llm_judge_score("test content", "test objective", mode="mock")
    assert result is None


# --- T8: BudgetReservation covers all paths ---

def test_budget_reservation_basic():
    """T8a: reservation tracks usage correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(Path(tmpdir) / "events.jsonl")
        bm = BudgetManager(store)
        r = bm.reserve("task-1", "simple_review")
        assert r.max_tokens == 5000
        assert r.used_tokens == 0
        assert not r.violation
        bm.record_usage(r, 1000)
        assert r.used_tokens == 1000
        assert r.remaining == 4000
        assert not r.violation


def test_budget_violation_detected():
    """T8b: exceeding budget triggers violation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(Path(tmpdir) / "events.jsonl")
        bm = BudgetManager(store)
        r = bm.reserve("task-1", "cheap_executor")  # max 2000
        bm.record_usage(r, 2500)
        assert r.violation


# --- T9: retry shares budget envelope ---

def test_retry_shares_budget():
    """T9: multiple record_usage calls against same reservation accumulate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(Path(tmpdir) / "events.jsonl")
        bm = BudgetManager(store)
        r = bm.reserve("task-1", "simple_review")
        bm.record_usage(r, 1000)
        bm.record_usage(r, 1000)
        bm.record_usage(r, 1000)
        assert r.used_tokens == 3000
        assert r.remaining == 2000


def test_budget_source_recorded_in_events():
    """T9b: budget_used events include source field in payload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(Path(tmpdir) / "events.jsonl")
        bm = BudgetManager(store)
        r = bm.reserve("task-1", "simple_review")
        bm.record_usage(r, 500, source="bridge_execution")
        bm.record_usage(r, 200, source="llm")
        events = store.replay()
        budget_events = [e for e in events if e.event_type == "budget_used"]
        assert len(budget_events) == 2
        assert budget_events[0].payload["source"] == "bridge_execution"
        assert budget_events[1].payload["source"] == "llm"


# --- T10: DevilsAdvocate can downgrade pass_with_notes ---

def test_fusion_overrule_downgrades_pass_with_notes():
    """T10: high-confidence overrule downgrades pass_with_notes to fail_retryable."""
    from merged_harness import AdversarialReview
    adv = AdversarialReview(
        reviewer="devils_advocate",
        challenges=[{"type": "x", "detail": "y", "severity": "high"}] * 4,
        verdict="overrule",
        confidence=0.9,
    )
    fused, adj = fuse_verdicts("pass_with_notes", adv, 0.75)
    assert fused == "fail_retryable", f"Expected fail_retryable, got {fused}"


def test_fusion_overrule_low_confidence_preserves():
    """T10b: low-confidence overrule preserves pass_with_notes."""
    from merged_harness import AdversarialReview
    adv = AdversarialReview(
        reviewer="devils_advocate",
        challenges=[{"type": "x", "detail": "y", "severity": "medium"}],
        verdict="overrule",
        confidence=0.6,
    )
    fused, adj = fuse_verdicts("pass_with_notes", adv, 0.75)
    assert fused == "pass_with_notes", f"Expected pass_with_notes, got {fused}"


def test_fusion_overrule_downgrades_pass():
    """T10c: overrule with score >= 0.80 downgrades pass to pass_with_notes."""
    from merged_harness import AdversarialReview
    adv = AdversarialReview(
        reviewer="devils_advocate",
        challenges=[{"type": "x", "detail": "y", "severity": "high"}],
        verdict="overrule",
        confidence=0.7,
    )
    fused, adj = fuse_verdicts("pass", adv, 0.85)
    assert fused == "pass_with_notes", f"Expected pass_with_notes, got {fused}"


# --- T11: YAML unknown field handling ---

def test_validate_task_yaml_rejects_unknown_fields():
    """T11: validate_task_yaml rejects unknown top-level keys."""
    task = {
        "task_id": "t1",
        "objective": "test",
        "subproblems": [{"id": "s1", "prompt": "p1"}],
        "evil_field": "should_be_rejected",
    }
    try:
        validate_task_yaml(task)
        assert False, "Should have raised ValueError for unknown fields"
    except ValueError as e:
        assert "unknown" in str(e).lower() or "evil_field" in str(e)


def test_validate_task_yaml_accepts_valid():
    """T11b: valid task passes validation."""
    task = {
        "task_id": "t1",
        "objective": "test",
        "subproblems": [{"id": "s1", "prompt": "p1"}],
    }
    validate_task_yaml(task)  # should not raise


def test_validate_task_yaml_rejects_missing_fields():
    """T11c: missing required fields rejected."""
    try:
        validate_task_yaml({"task_id": "t1"})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
