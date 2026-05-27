# Token Furnace Methodology

## Definition

Token Furnace is a controlled high-token experimental method for converting large model interaction cost into durable engineering assets.

It is not "burning tokens for more answers." It is:

```text
high-token exploration
+ constrained experiment protocol
+ multi-model cross-audit
+ structured evidence
+ matrix-based verdicts
+ regression and knowledge deposition
= reusable engineering progress
```

## Core Problem

Large-token AI workflows often fail because they produce long conversations but weak artifacts. Token Furnace exists to prevent that failure mode.

## Core Principles

### 1. Token cost must become assets

Every expensive run should produce at least one of:
- matrix
- test
- decision record
- failure record
- reusable prompt
- wiki note
- regression script
- closeout report

### 2. Experiment completion is not target success

Always separate:

```yaml
experiment_verdict: COMPLETE | INCOMPLETE
target_control_verdict: PASS | PASS_WITH_NOTES | FAIL
```

For phase closeout, also separate:

```yaml
phase_verdict:
target_control_verdict:
platform_validation_verdict:
```

### 3. Healthy failure is valid

An experiment can succeed by proving the target fails.

```yaml
experiment_verdict: COMPLETE
target_control_verdict: FAIL
```

### 4. Model agreement is not evidence

Model agreement is a signal. Matrix evidence is the verdict source.

### 5. Path-aware systems need path-aware matrices

If a target has multiple execution paths, each path must be evaluated separately.

```yaml
marker_executor:
  status: pass
worker_daemon:
  status: fail
```

### 6. Conformance is not safety

Two paths can be conformant because both are missing the same control. Conformance pass must not automatically imply safety pass.

### 7. Fixes need regression

A fix is not stable until it is locked by a repeatable test or validator.

### 8. Knowledge deposition is part of the experiment

A run is incomplete if findings are not deposited into reusable knowledge.

## Standard Lifecycle

```text
audit
→ verification
→ fix
→ regression
→ refactor
→ ingress/runtime audit
→ hardening
→ closeout
```

## Roles

### Claude Code / Local Executor

- reads repo
- implements tests/fixes
- collects grounded evidence
- runs commands
- reports dirty state

### GPT / Architecture Reviewer

- audits assumptions
- designs experiment structure
- separates verdict types
- detects methodology drift
- produces synthesis and next-step judgment

### Codex / Code Risk Reviewer

- checks implementation risks
- finds weak assertions
- audits bypass paths
- reviews patches and regressions

## Required Artifacts

### Per Experiment

- experiment.yaml
- task.md
- model outputs
- matrix
- synthesis
- run artifacts

### Per Phase

- phase closeout
- final matrices
- decision records
- failure records
- regression commands
- tag / commit reference

## Verdict System

### Experiment Verdict

Did the experiment run correctly?

### Target Control Verdict

Is the target control actually acceptable?

### Platform Validation Verdict

Did Token Furnace methodology prove useful?

## Matrix System

Matrices must track:
- case id
- expected behavior
- actual behavior
- affected path/component
- evidence type
- evidence path
- assertion strength
- status
- follow-up

## Evidence Types

```text
static_inspection
unit_test
integration_test
runtime_trace
manual_review
model_inference
```

Model inference alone must not justify PASS.

## Phase 1 Case: hermes-perm-audit

### What Phase 1 Proved

- Multi-model audit found policy-runtime drift.
- Path-aware matrix exposed worker/marker divergence.
- Fixes restored behavior.
- Regression suite locked the fix.
- Shared gate policy removed duplicated authority logic.
- Queue ingress audit found remaining warnings.
- Queue hardening improved resilience.
- Closeout made the phase reproducible.

### Main Lesson

The system was not verified when one path denied. It became credible only after every execution path was tested, repaired, and locked by regression.

## Reusable Patterns

### Pattern: Dual Verdict

Use when an experiment can succeed by finding a failure.

### Pattern: Path-Aware Matrix

Use when there are multiple execution paths or components.

### Pattern: Revised Finding

Use when a model finding is directionally useful but technically imprecise.

### Pattern: Healthy Failure

Use when FAIL is the expected useful outcome.

### Pattern: Fix-Then-Regress

Use when a safety defect is repaired.

## Anti-Patterns

### Long conversation without artifact

A token sink, not a Token Furnace run.

### Model consensus as verdict

Agreement is not proof.

### Global PASS from single-path evidence

Unsafe in multi-path systems.

### Fix without regression

Temporary repair, not durable control.

### Conformance treated as safety

Two components can agree on the same missing control.

## When To Use Token Furnace

Use it for:
- permission systems
- agent runtimes
- MCP/tool boundaries
- local execution pipelines
- multi-model workflow audits
- long-context repo/process audits
- benchmark and regression design

Do not use it for:
- simple Q&A
- one-off edits
- low-risk documentation cleanup
- tasks where artifact overhead exceeds value

## Next Methodology Improvements

- machine-checkable run verdict files
- matrix consistency validator
- reusable prompt library
- automated artifact completeness checks
