# ArXiv Seed Corpus

This corpus is for pipeline validation, not final engineering evidence for the 22µF DC-Link water-pump design.

## Papers

| ID | Filename | arXiv ID | Category | Purpose |
|----|----------|----------|----------|---------|
| A1 | A1-sensorless-foc-csi-pmsm-submersible-pump.pdf | 2503.22855 | P1 (Algorithm) | Sensorless FOC for CSI-fed PMSM in submersible pumps |
| A2 | A2-pmsm-smo-sensorless-vector-control.pdf | 2305.04046 | P2 (Engineering) | Sliding mode observer for PMSM sensorless vector control |
| A3 | A3-dc-link-ripple-harmonics-feedback.pdf | 1901.10020 | P3 (Comparison) | Boost converter with low output ripple based on harmonics feedback |

## Source

Downloaded from arXiv on 2026-05-27.

## Purpose

Phase 4 benchmark: validate Token Furnace Lab's ability to extract structured algorithm information from technical PDFs.

## Next Steps

1. Run PDF inventory: `python3 scripts/pdf_inventory.py papers/arxiv-seed/`
2. Verify text extractability
3. Select papers for algorithm card extraction
