# Next Experiment: After hermes-perm-audit-008

## Status

Phase 1 concluded. No further Hermes hardening recommended.

## Recommended Next Steps

### Priority 1: Methodology Templates

Create reusable templates from Phase 1 learnings:

| Template | Purpose |
|----------|---------|
| `docs/methodology/token-furnace-experiment-lifecycle.md` | Full lifecycle guide |
| `templates/experiment.yaml` | Experiment definition template |
| `templates/synthesis.md` | Synthesis output template |
| `templates/matrix.yaml` | Matrix template |
| `templates/phase-closeout.md` | Phase closeout template |
| `knowledge/wiki/token-furnace-methodology.md` | Methodology wiki |

### Priority 2: Phase 2 Planning (if desired)

If continuing, choose a different target to validate generalization:

| Target | Type | Effort |
|--------|------|--------|
| OpenClaw runtime permission audit | Security audit | Medium |
| MCP bridge tool-boundary audit | Security audit | Medium |
| Claude/Codex workflow quality-gate audit | Quality audit | Medium |
| PDF-to-algorithm extraction benchmark | Benchmark | Large |

### Phase 2 Selection Criteria

1. **Different domain**: Not another permission audit
2. **Reusable methodology**: Can apply audit → verify → fix → regress pattern
3. **Measurable outcomes**: Clear success criteria
4. **Token justification**: High consumption must produce real assets

## Known Gaps (Low Priority)

| ID | Issue | Severity | Recommendation |
|----|-------|----------|----------------|
| Q003 | No integrity check on queue items | Low | Defer unless file tampering is concern |
| Q005 | No approval TTL | Low | Arm gate consumption is actual protection |

## Methodology Insights

From GPT:
> "这轮最重要的成果不是 Hermes 修了多少点，而是 Token Furnace Lab 的工作流被验证了"

The workflow pattern:
```
audit → verify → fix → regress → refactor → ingress audit → harden → closeout
```

This converts high token consumption into:
- Reproducible experiment records
- Multi-model audit outputs
- Security matrices
- Regression suites
- Shared policies
- Knowledge base
