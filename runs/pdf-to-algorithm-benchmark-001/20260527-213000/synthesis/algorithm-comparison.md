# Algorithm Comparison — Phase 4 Run 001

## Overview

3 papers compared across 8 dimensions relevant to 22µF DC-link + sensorless FOC + water pump project.

## Comparison Matrix

| Dimension | A1 (CSI-Fed FOC) | A2 (SMO Vector) | A3 (Boost Ripple) |
|-----------|:-:|:-:|:-:|
| **Topology** | CSI-fed PMSM | VSI PMSM (simulation) | Boost converter + inverter |
| **Control Type** | Sensorless FOC | Sensorless FOC | Duty-cycle feedback |
| **Observer** | PLL + back-EMF | Sliding mode observer | 7th-order LTI harmonic |
| **Startup** | I-f → FOC (3-step) | Not addressed | Not addressed |
| **DC-Link Ripple** | Not addressed | Not addressed | Primary focus |
| **Pavg_ref** | Not found | Not found | Not found |
| **Sensors** | Current only (sensorless) | Current only (sensorless) | Voltage + current |
| **MCU Platform** | TMS320F28388D | Simulation only | 18kHz sampling |

## Key Equations Comparison

| Equation Type | A1 | A2 | A3 |
|---------------|----|----|-----|
| Motor model | αβ + dq voltage | αβ voltage + back-EMF | N/A |
| Observer | PLL tracking | SMO switching + LPF | 7th-order LTI |
| Position est. | Error compensation | arctan + compensation | N/A |
| Speed control | N/A (startup only) | PI + active damping | N/A |
| Ripple control | N/A | N/A | Harmonic feedback |

## Parameter Comparison

| Parameter | A1 | A2 | A3 |
|-----------|----|----|-----|
| Voltage | 480V grid | 220V rated | 12V/28V |
| Power | Not stated | 200W | Not stated |
| Speed | 300rpm | 3000rpm | N/A |
| Capacitance | 50µF output | N/A | N/A |
| Switching freq | Not stated | 10kHz | 18kHz |
| Cable length | 1.8km | N/A | N/A |

## Applicability to Target Scenario

| Requirement | A1 | A2 | A3 | Gap |
|-------------|:--:|:--:|:--:|-----|
| Sensorless FOC | ✓ | ✓ | ✗ | Need VSI adaptation for A1 |
| Small DC-link (22µF) | ✗ | ✗ | Partial | No paper validates 22µF |
| Pump startup | ✓ | ✗ | ✗ | A1 directly applicable |
| Pavg_ref calculation | ✗ | ✗ | ✗ | Need separate source |
| Power ripple suppression | ✗ | ✗ | ✓ | A3 provides observer concept |
| TMS320F28035 feasibility | ✓ (28388D) | Unknown | Unknown | Need computational analysis |

## Synthesis

**Combined approach**: The three papers provide complementary pieces:
1. **A1**: Startup strategy and sensorless transition (adapt for VSI)
2. **A2**: SMO observer structure and PI tuning (implement on F28035)
3. **A3**: DC-link harmonic observer concept (adapt for inverter-side)

**Critical gaps**: None of the papers address the full target scenario (22µF DC-link + sensorless FOC + pump + VSI). A fourth paper or custom derivation is needed.
