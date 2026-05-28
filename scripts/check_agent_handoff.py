#!/usr/bin/env python3
"""Validate the autonomous research handoff surface."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SNIPPETS = {
    "AGENTS.md": [
        "Autonomous Advancement Authority",
        "Autonomous Research Loop",
        "Documentation Maintenance Rule",
    ],
    "CLAUDE.md": [
        "自主推进协议",
        "scripts/check_agent_handoff.py",
        "GPT final PASS_WITH_NOTES",
    ],
    "README.md": [
        "autonomously advance research tasks",
        "scripts/check_agent_handoff.py",
    ],
    "docs/SESSION_START_HERE.md": [
        "GPT_FINAL_PASS_WITH_NOTES",
        "Autonomous Research Closeout",
        "Latest sealed run:",
    ],
    "docs/runs/token-furnace-current-state.md": [
        "GPT_FINAL_PASS_WITH_NOTES",
        "Responsible coding agents may autonomously advance",
    ],
}


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _latest_run_from_session_doc(text: str) -> str | None:
    match = re.search(r"Latest sealed run:\s*`([^`]+)`", text)
    return match.group(1) if match else None


def main() -> int:
    failures: list[str] = []

    for relative_path, snippets in REQUIRED_SNIPPETS.items():
        path = ROOT / relative_path
        if not path.exists():
            failures.append(f"missing required handoff file: {relative_path}")
            continue

        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                failures.append(f"{relative_path} is missing required text: {snippet!r}")

    session_doc = _read("docs/SESSION_START_HERE.md")
    latest_run = _latest_run_from_session_doc(session_doc)
    if not latest_run:
        failures.append("docs/SESSION_START_HERE.md does not declare a latest sealed run")
    else:
        run_dir = ROOT / latest_run
        if not run_dir.is_dir():
            failures.append(f"latest sealed run does not exist: {latest_run}")
        else:
            for required in ("task.md", "run.yaml", "status.md"):
                if not (run_dir / required).exists():
                    failures.append(f"latest sealed run is missing {required}: {latest_run}")

            status_text = (run_dir / "status.md").read_text(encoding="utf-8")
            run_yaml_text = (run_dir / "run.yaml").read_text(encoding="utf-8")
            if "GPT_FINAL_PASS_WITH_NOTES" not in status_text:
                failures.append(f"{latest_run}/status.md does not reflect GPT final status")
            if "GPT_FINAL_PASS_WITH_NOTES" not in run_yaml_text:
                failures.append(f"{latest_run}/run.yaml does not reflect GPT final status")

    for relative_path in (
        "AGENTS.md",
        "CLAUDE.md",
        "docs/SESSION_START_HERE.md",
        "docs/runs/token-furnace-current-state.md",
    ):
        text = _read(relative_path)
        if "GPT final pending" in text or "still pending GPT final verification" in text:
            failures.append(f"{relative_path} still says GPT final verification is pending")

    if failures:
        print("Agent handoff check FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Agent handoff check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
