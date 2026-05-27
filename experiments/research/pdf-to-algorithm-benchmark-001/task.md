# PDF-to-Algorithm Extraction Benchmark — Task Definition

## Objective

Validate whether Token Furnace Lab can generalize from agent security auditing to structured research extraction. Specifically: extract verifiable, comparable, implementable algorithm information from specialized Chinese technical PDFs on motor control.

## Scope

- **Domain**: Electrolytic-capacitorless drive / small DC-Link capacitance / FOC
- **Corpus**: 3 local Chinese technical PDFs (P1: algorithm, P2: engineering, P3: comparison)
- **Extraction**: Structured algorithm cards with formulas, control logic, experimental conditions, applicability boundaries

## Key Extraction Questions

1. How is Pavg_ref (power reference) calculated?
2. How does DC-Link voltage ripple enter the control loop?
3. How is torque/speed ripple suppressed with small capacitance?
4. How is input/output power balanced?
5. What sensors are required (voltage/current/speed)?
6. Is it suitable for sensorless FOC?
7. Is it feasible on TMS320F28035?
8. Is the algorithm realistic for 22µF DC-Link?

## Model Roles

| Model | Role | Output |
|-------|------|--------|
| Claude Code | PDF reader, inventory generator | claude-code-pdf-reader.md |
| GPT | Algorithm card extractor | gpt-algorithm-cards.md |
| Codex | Implementation feasibility reviewer | codex-implementation-review.md (optional) |

## Evaluation (5 dimensions, 100 points)

| Dimension | Weight | Focus |
|-----------|--------|-------|
| Accuracy | 30 | Formulas, variables, conditions correct; no inference-as-fact |
| Completeness | 20 | Problem, algorithm, formulas, experiments, boundaries covered |
| Implementability | 25 | Convertible to pseudocode, control flow, or engineering plan |
| Evidence Quality | 15 | Page numbers, figure/table/formula references for key claims |
| Project Relevance | 10 | Serves 22µF DC-Link + sensorless FOC + pump scenario |

## Verdict Criteria

- **PASS**: Implementable algorithm flow with page/formula/figure evidence
- **PASS_WITH_NOTES**: Useful direction but missing parameters, incomplete formulas, insufficient experiments
- **FAIL**: Summary only, not convertible to algorithm; or missing evidence; or hallucinations

## Deliverables

1. PDF inventory (scan local corpus)
2. Paper selection (3 papers with justification)
3. Algorithm cards (one per paper)
4. Extraction quality report
5. Algorithm comparison matrix
6. Project relevance ranking

## Constraints

- No more than 3 papers in first round
- No review/survey papers (poor algorithm落地性)
- At least one Chinese paper
- At least one engineering-focused paper
- PDF must have copyable text and clear figures
