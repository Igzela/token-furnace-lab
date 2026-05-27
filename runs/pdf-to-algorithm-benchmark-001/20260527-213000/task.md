# PDF-to-Algorithm Extraction Benchmark — Run 001

## Objective

Validate Token Furnace Lab's ability to extract structured algorithm information from technical PDFs on motor control / FOC.

## Source Corpus

- **A1**: Sensorless FOC for CSI-fed PMSM in submersible pumps (2503.22855)
- **A2**: SMO-based sensorless PMSM vector control (2305.04046)
- **A3**: Boost converter with low output ripple via harmonics feedback (1901.10020)

## Model Roles

| Model | Role | Output |
|-------|------|--------|
| Claude Code | PDF reader, inventory generator | claude-code-pdf-reader.md |
| GPT | Algorithm card extractor | gpt-algorithm-cards.md |
| Codex | Implementation feasibility reviewer | codex-implementation-review.md (optional) |

## Key Extraction Questions

1. How is Pavg_ref (power reference) calculated?
2. How does DC-Link voltage ripple enter the control loop?
3. How is torque/speed ripple suppressed with small capacitance?
4. How is input/output power balanced?
5. What sensors are required?
6. Is it suitable for sensorless FOC?
7. Is it feasible on TMS320F28035?
8. Is the algorithm realistic for 22µF DC-Link?

## Evaluation (5 dimensions, 100 points)

| Dimension | Weight | Focus |
|-----------|--------|-------|
| Accuracy | 30 | Formulas, variables, conditions correct |
| Completeness | 20 | Problem, algorithm, formulas, experiments covered |
| Implementability | 25 | Convertible to pseudocode or engineering plan |
| Evidence Quality | 15 | Page numbers, figure/table references |
| Project Relevance | 10 | Serves 22µF DC-Link + sensorless FOC + pump |

## Current Status

- [x] PDF inventory
- [x] Paper selection
- [x] Claude Code PDF reader output
- [ ] GPT algorithm card extraction
- [ ] Codex implementation review
- [ ] Extraction quality report
- [ ] Algorithm comparison matrix
