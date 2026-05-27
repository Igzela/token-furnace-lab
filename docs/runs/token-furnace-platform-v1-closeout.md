# Token Furnace Lab — Platform v1 Closeout

## Metadata

- Platform: Token Furnace Lab v1
- Status: CONSOLIDATED
- Created: 2026-05-28

## Validated Baselines

| Baseline | Type | Verdict | Tag |
|----------|------|---------|-----|
| hermes-perm-audit-phase-1 | Deep control-plane audit | PASS_WITH_NOTES | hermes-perm-audit-phase-1 |
| mcp-bridge-boundary-audit-phase-1 | Cross-project boundary audit | PASS | mcp-bridge-boundary-audit-phase-1 |
| token-furnace-methodology-v1 | Reusable methodology | Platform validated | token-furnace-methodology-v1 |

## Validated Capabilities

### 1. Multi-Model Cross-Audit
- **Status**: VALIDATED
- **Evidence**: Both phases used GPT (architect) + Claude Code (implementer) pattern
- **Hermes**: GPT designed audit matrix, Claude Code implemented fixes
- **MCP Bridge**: GPT designed boundary matrix, Claude Code wrote fixture tests

### 2. 8-Phase Experiment Lifecycle
- **Status**: VALIDATED
- **Evidence**: Hermes Phase 1 completed full lifecycle (audit → verify → fix → regress → refactor → ingress audit → harden → closeout)
- **MCP Bridge**: Completed audit + verify phases

### 3. Dual Verdict System
- **Status**: VALIDATED
- **Evidence**: Both phases used experiment_verdict + target_control_verdict
- **Hermes**: COMPLETE / PASS_WITH_NOTES
- **MCP Bridge**: COMPLETE / PASS

### 4. Matrix-Based Evidence Collection
- **Status**: VALIDATED
- **Evidence**: Both phases produced conformance matrices with status tracking
- **Hermes**: Permission matrix with path-aware status
- **MCP Bridge**: 16-case boundary matrix with runtime verification

### 5. Knowledge Distillation
- **Status**: VALIDATED
- **Evidence**: Both phases produced wiki, decisions, evaluator-rules, matrices
- **Reusable**: Knowledge assets can be referenced in future audits

### 6. Cross-Project Generalization
- **Status**: VALIDATED
- **Evidence**: MCP Bridge audit applied same methodology to different codebase
- **Proof**: Not a one-project success

## Risk Types Covered

| Risk Type | Hermes | MCP Bridge |
|-----------|--------|------------|
| Permission escalation | ✅ | — |
| Path traversal | ✅ | ✅ |
| Input validation | ✅ | ✅ |
| Hidden tool exposure | — | ✅ |
| Subprocess lifecycle | — | ✅ |
| Session isolation | — | ✅ |
| Audit leakage | ✅ | ✅ |
| Argument injection | — | ✅ |

## Stable Templates and Mechanisms

| Asset | Status | Reusable |
|-------|--------|----------|
| templates/experiment.yaml | STABLE | ✅ |
| templates/synthesis.md | STABLE | ✅ |
| templates/matrix.yaml | STABLE | ✅ |
| templates/phase-closeout.md | STABLE | ✅ |
| Dual verdict system | STABLE | ✅ |
| Matrix status tracking | STABLE | ✅ |
| Knowledge distillation | STABLE | ✅ |

## Unvalidated Capabilities

1. **Public internet exposure**: No Cloudflare tunnel / external network testing
2. **Multi-user auth model**: No real authentication/authorization testing
3. **Long-term stability**: No extended runtime / stress testing
4. **Real production deployment**: No production environment testing
5. **Malicious local process**: No same-user process tampering testing

## Phase 3 Target Selection Criteria

Based on validated capabilities, Phase 3 should:

1. **Expand risk coverage**: Target a system with different risk profile (e.g., network exposure, multi-user)
2. **Test unvalidated capabilities**: Choose target that requires public internet or auth testing
3. **Maintain methodology reuse**: Apply same lifecycle, templates, verdict system
4. **Produce new knowledge assets**: Generate domain-specific evaluator rules

Recommended targets:
- **Option A**: Cloudflare tunnel security audit (tests network exposure)
- **Option B**: Multi-user permission model audit (tests auth/authorization)
- **Option C**: Long-running service stability audit (tests production readiness)

## Platform Maturity Assessment

| Dimension | Level | Evidence |
|-----------|-------|----------|
| Methodology reuse | L3-VALIDATED | 2 successful cross-project applications |
| Template stability | L3-VALIDATED | All templates used without modification |
| Verdict mechanism | L3-VALIDATED | Dual verdicts consistently applied |
| Knowledge distillation | L2-PROVEN | Assets produced, reuse pending |
| Cross-project generalization | L3-VALIDATED | Different codebase, same methodology |

**Overall Platform Maturity: L3-VALIDATED**

## Tag

```
git tag token-furnace-platform-v1
```
