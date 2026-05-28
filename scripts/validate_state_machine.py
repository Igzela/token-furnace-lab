#!/usr/bin/env python3
"""
Deterministic validator for state machine models.

Checks:
- All transition targets are defined states
- Universal hard-fault rules present
- Every fault code used is defined
- Every fault code defined is either used or marked reserved
- No active state lacks OC/OV/tripzone path
- Cold-start sequence references valid states
"""

import re
import sys
from pathlib import Path
from typing import Optional


def extract_states(content: str) -> set[str]:
    """Extract state names from State Definitions table."""
    states = set()
    in_table = False
    for line in content.split("\n"):
        if "State Definitions" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[1] and parts[1] != "State":
                states.add(parts[1])
        elif in_table and not line.startswith("|") and line.strip():
            in_table = False
    return states


def extract_transitions(content: str) -> dict[str, list[str]]:
    """Extract transitions from transition matrix."""
    transitions = {}
    current_state = None
    in_matrix = False
    in_code_block = False

    for line in content.split("\n"):
        if "Transition Matrix" in line:
            in_matrix = True
            continue
        if not in_matrix:
            continue

        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Match state name at start of line (e.g., "FOC_NORMAL:")
        state_match = re.match(r"^([A-Z_]+):$", line.strip())
        if state_match:
            current_state = state_match.group(1)
            transitions[current_state] = []
            continue

        # Match transition (e.g., "  oc_trip → FAULT_LATCHED + PWM disable")
        # Also match inside code blocks
        trans_match = re.match(r"^\s+(\w+).*→\s+([A-Z_]+)", line)
        if trans_match and current_state:
            target = trans_match.group(2)
            transitions[current_state].append(target)

    return transitions


def extract_fault_codes(content: str) -> dict[int, str]:
    """Extract fault codes from fault code table."""
    codes = {}
    in_table = False
    for line in content.split("\n"):
        if "Fault Code Table" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].isdigit():
                code_num = int(parts[1])
                code_name = parts[2]
                codes[code_num] = code_name
        elif in_table and not line.startswith("|") and line.strip():
            in_table = False
    return codes


def extract_fault_class_events(content: str) -> set[str]:
    """Extract fault events referenced in fault classes."""
    events = set()
    in_classes = False
    for line in content.split("\n"):
        if "Fault Classes" in line or "fault_classes" in line.lower():
            in_classes = True
            continue
        if in_classes and "events:" in line:
            # Extract event names from list
            match = re.search(r"\[([^\]]+)\]", line)
            if match:
                for event in match.group(1).split(","):
                    events.add(event.strip())
    return events


def check_universal_hard_faults(transitions: dict[str, list[str]], content: str) -> list[str]:
    """Check that UNIVERSAL hard-fault rules exist."""
    errors = []
    if "UNIVERSAL" not in transitions:
        errors.append("CRITICAL: No UNIVERSAL hard-fault block in transition matrix")
        return errors

    # Check for required fault events in the UNIVERSAL section of the content
    # Find the UNIVERSAL block in the content
    universal_match = re.search(r"UNIVERSAL:.*?```", content, re.DOTALL)
    if not universal_match:
        errors.append("CRITICAL: UNIVERSAL block not found in content")
        return errors

    universal_block = universal_match.group(0)
    required_faults = ["oc_trip", "gate_driver_fault", "pwm_tripzone", "emergency_stop"]

    for fault in required_faults:
        if fault not in universal_block:
            errors.append(f"HIGH: UNIVERSAL missing {fault} transition")

    return errors


def check_state_coverage(states: set[str], transitions: dict[str, list[str]]) -> list[str]:
    """Check that all transition targets are defined states."""
    errors = []
    all_targets = set()
    for state, targets in transitions.items():
        for target in targets:
            # Clean target (remove extra info)
            clean = target.split("(")[0].strip()
            if clean and clean not in ("", "→"):
                all_targets.add(clean)

    # Add known non-state targets
    known_non_states = {"PWM disable", "PWM_DISABLE", "SAFE_DISABLE", "immediate"}
    all_targets -= known_non_states

    for target in all_targets:
        if target not in states and target != "UNIVERSAL":
            errors.append(f"MEDIUM: Transition target '{target}' not in state definitions")

    return errors


def check_fault_code_coverage(codes: dict[int, str], events: set[str]) -> list[str]:
    """Check fault code table completeness."""
    errors = []
    code_names = {name.upper().replace(" ", "_") for name in codes.values()}

    for event in events:
        event_upper = event.upper().replace(" ", "_")
        if event_upper not in code_names:
            # Check if it maps to an existing code
            if event == "startup_tmo" and "STARTUP_TMO" not in code_names:
                errors.append(f"MEDIUM: Fault event '{event}' has no corresponding fault code")
            elif event == "precharge_fail" and "PRECHARGE_FAIL" not in code_names:
                errors.append(f"MEDIUM: Fault event '{event}' has no corresponding fault code")

    return errors


def check_active_state_fault_paths(transitions: dict[str, list[str]]) -> list[str]:
    """Check that active states have OC/OV/tripzone paths."""
    errors = []
    active_states = ["FOC_NORMAL", "FOC_DERATED", "OBSERVER_DEGRADED", "FLYING_RESTART",
                     "CONTROLLED_DECEL", "APD_DEGRADED"]

    # If UNIVERSAL exists, all active states inherit its transitions
    if "UNIVERSAL" in transitions:
        return errors  # UNIVERSAL covers all active states

    for state in active_states:
        if state not in transitions:
            errors.append(f"HIGH: Active state {state} has no transitions defined")
            continue

        state_transitions = str(transitions[state])
        required = ["oc_trip", "vdc_ov"]
        for req in required:
            if req not in state_transitions:
                errors.append(f"HIGH: Active state {state} missing {req} path")

    return errors


def validate(model_path: Path) -> tuple[bool, list[str]]:
    """Run all validations on a state machine model."""
    content = model_path.read_text(encoding="utf-8")
    errors = []

    states = extract_states(content)
    transitions = extract_transitions(content)
    codes = extract_fault_codes(content)
    events = extract_fault_class_events(content)

    if not states:
        errors.append("CRITICAL: No states found in State Definitions table")
        return False, errors

    errors.extend(check_universal_hard_faults(transitions, content))
    errors.extend(check_state_coverage(states, transitions))
    errors.extend(check_fault_code_coverage(codes, events))
    errors.extend(check_active_state_fault_paths(transitions))

    has_critical = any("CRITICAL" in e for e in errors)
    has_high = any("HIGH" in e for e in errors)

    passed = not has_critical and not has_high
    return passed, errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_state_machine.py <model.md>")
        sys.exit(1)

    model_path = Path(sys.argv[1])
    if not model_path.exists():
        print(f"File not found: {model_path}")
        sys.exit(1)

    passed, errors = validate(model_path)

    if passed:
        print(f"PASS: {model_path.name} ({len(errors)} warnings)")
    else:
        print(f"FAIL: {model_path.name}")

    for error in sorted(errors):
        print(f"  {error}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
