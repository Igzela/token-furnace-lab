# Token Furnace Lab — Cross-Phase Lessons Learned

## Overview

Lessons learned from Hermes Phase 1 and MCP Bridge Phase 1, extracted for methodology hardening.

## Lesson 1: Static → Mock → Runtime Progression Works

**Observation**: Both phases benefited from layered verification:
- Static analysis discovers structure
- Mock verification confirms logic
- Runtime fixtures verify behavior

**Evidence**:
- MCP Bridge 001: Static + mock (7 tests)
- MCP Bridge 002: Runtime fixtures (8 tests)
- Combined: 16/16 PASS

**Rule**: Always start with static analysis, then mock, then runtime. Don't skip layers.

## Lesson 2: GPT as Architect + Claude Code as Implementer

**Observation**: Role separation produces better results than single-model execution.

**Evidence**:
- GPT designed 16-case boundary matrix for MCP Bridge
- Claude Code wrote 15 fixture tests
- GPT confirmed verdicts and identified gaps

**Rule**: Use GPT for architecture/design, Claude Code for implementation/testing.

## Lesson 3: Dual Verdicts Prevent Premature Closure

**Observation**: Separate experiment_verdict and target_control_verdict forces honest assessment.

**Evidence**:
- MCP Bridge 001: COMPLETE / PASS_WITH_NOTES (not full PASS)
- MCP Bridge 002: COMPLETE / PASS (upgraded after runtime verification)

**Rule**: Never give full PASS without runtime evidence. PASS_WITH_NOTES is honest.

## Lesson 4: Matrices Track Progress Better Than Narratives

**Observation**: Matrix status tracking (PASS/PARTIAL/UNKNOWN) is clearer than prose.

**Evidence**:
- MCP Bridge matrix: 16 cases, each with status
- Easy to see what's done (PASS) vs. what's pending (UNKNOWN/PARTIAL)

**Rule**: Always produce a matrix. Status tracking prevents hidden gaps.

## Lesson 5: Knowledge Assets Must Be Reusable

**Observation**: Knowledge distillation only pays off if assets are reusable.

**Evidence**:
- Evaluator rules: `ER-mcp-hidden-tools-deny-before-forward.md` can be applied to any MCP bridge
- Decision records: `DR-mcp-bridge-readonly-allowlist-boundary.md` documents design rationale

**Rule**: Write knowledge assets as if someone else will apply them to a different project.

## Lesson 6: Closeout Prevents Drift

**Observation**: Without closeout, experiments tend to expand scope indefinitely.

**Evidence**:
- MCP Bridge 001: GPT said "don't add runtime tests to 001"
- MCP Bridge 002: GPT said "closeout, don't add tunnel testing"

**Rule**: Close each phase explicitly. Document what's NOT in scope.

## Lesson 7: Cross-Project Proof Requires Different Codebases

**Observation**: One successful project could be luck. Two proves methodology.

**Evidence**:
- Hermes: Python permission system
- MCP Bridge: Python HTTP/stdio bridge
- Different domains, same methodology success

**Rule**: At least 2 successful applications before claiming methodology validity.

## Anti-Patterns Observed

1. **Scope creep**: Temptation to add more tests to an already-complete phase
2. **Premature expansion**: Wanting to start Phase 3 before consolidating Phase 1+2
3. **Template deviation**: Temptation to skip templates for "quick" experiments
4. **Single-model execution**: Using one model for both design and implementation

## Methodology Hardening Recommendations

1. **Enforce closeout gates**: Don't start new phase until previous is tagged
2. **Require matrix**: Every experiment must produce a conformance matrix
3. **Require dual verdicts**: experiment_verdict + target_control_verdict always
4. **Require knowledge assets**: At least 1 wiki + 1 decision record per phase
5. **Document anti-patterns**: Record what NOT to do, not just what to do
