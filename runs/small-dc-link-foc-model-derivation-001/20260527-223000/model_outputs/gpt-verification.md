# GPT Verification — Pavg_ref and 22µF DC-Link Ripple Derivation

## Metadata

- Experiment: small-dc-link-foc-model-derivation-001
- Model: GPT (ChatGPT)
- Role: Independent mathematical verification + engineering judgment
- Date: 2026-05-27

## Verdict

**Equations are correct. Engineering feasibility assessment is correct. Key refinement: Pavg_ref should include loss offset term.**

## Q1: Single-Phase Ripple Formula

$$\Delta V_{dc} \approx \frac{I_{load}}{2 \cdot f_{grid} \cdot C_{dc}}$$

**Verdict: Formula correct** under 4 assumptions:
1. Load approximately constant current
2. Capacitor discharges between rectification peaks
3. Ripple is much smaller than bus voltage
4. Rectification peaks can periodically recharge capacitor

Claude Code's arithmetic is correct: 545V. But 545V > 300V means the small-ripple assumption **collapses**. The bus is not "300V + ripple" but rather approaches the rectified pulse voltage / collapsing bus.

**Critical clarification**: I_load = 1.2A must be DC bus average current, not motor phase current. P_dc ≈ 300V × 1.2A = 360W.

## Q2: Single-Phase 22µF Physical Infeasibility

**Verdict: Infeasible** for passive rectification + 22µF + 360W + stable DC bus.

GPT provides reverse calculation:
- For 10% ripple (30V), C_needed ≈ 400µF
- For 22µF at 10% ripple: I_max ≈ 0.066A, P_max ≈ 20W

**22µF can work only under these conditions:**
1. Very low power
2. Allow large 100/120 Hz bus swing
3. Control algorithm actively adapts to bus ripple
4. APD / active buffer / mechanical inertia absorption
5. Three-phase input or other continuous supply

## Q3: Three-Phase Ripple Formula

$$\Delta V_{dc} \approx \frac{I_{load}}{6 \cdot f_{grid} \cdot C_{dc}}$$

**Verdict: Formula direction correct** (three-phase rectification peak frequency is 6f_grid). Arithmetic correct: 182V. But 182V/300V is still outside small-ripple working region. Three-phase is much better than single-phase, but 22µF at 360W is still small-capacity DC-Link.

## Q4: Pump Affinity Laws

**Verdict: Valid first-order model.**

P ∝ ω³ relationship holds for centrifugal pumps under similar conditions (same impeller, same fluid, similar operating point).

**Engineering refinements needed:**
1. Low-speed friction, bearings, seals break pure cubic relationship
2. Static head present → pump load no longer strictly follows affinity law
3. η is not constant — varies with speed, load, motor/inverter efficiency
4. Better form: P_avg_ref(ω) = P₀ + k·ω³ where P₀ covers friction, iron losses, controller losses, no-load losses

## Q5: APD 20dB @ 100Hz Feasibility

**Verdict: Possible but requires real energy buffer.**

GPT's energy analysis:
- E_buf ≈ P/(4πf) ≈ 0.57J (required for 360W, 50Hz)
- E_total = 0.5·C·V² ≈ 0.99J (22µF at 300V)
- E_usable ≈ C·V·ΔV_peak ≈ 0.099J (if ±15V allowed)

**E_usable << E_buf** — energy deficit. APD cannot eliminate 100Hz energy without a real energy path:
1. Additional active buffer capacitor/inductor
2. Front-end PFC / active rectification
3. Allow motor power to swing at 100Hz, absorbed by mechanical inertia
4. Sacrifice torque/speed ripple
5. Power-limited operation

**Warning on linear division**: 545V/10 = 54.5V is mathematically 20dB reduction, but 545V is already in the formula-failure zone. Cannot treat it as real linear ripple then divide by 10. More reasonable: if APD can reduce equivalent 2x-frequency bus energy swing by 10x, then 22µF may produce ~tens-of-volts bus ripple — difficult but not uncontrollable.

54.5Vpp / 300V ≈ 18%pp ≈ ±9%: feasible for sensorless FOC **only with** Vdc real-time sampling, SVPWM voltage feedforward, current limiting, observer robustness design.

## Q6: SMO Sensorless FOC Voltage Ripple Tolerance

**Verdict: No universal fixed value. < 10%pp is a reasonable conservative target.**

SMO robustness depends on:
1. Vdc real-time sampling used for SVPWM / voltage reconstruction
2. Current loop bandwidth
3. Observer bandwidth and LPF parameters
4. Motor speed (low speed = low back-EMF = most vulnerable)
5. Dead-time, sampling delay, parameter errors
6. Modulation saturation
7. Minimum bus voltage still provides required back-EMF and current regulation margin

**Experience-based grading:**
| Ripple %pp | Assessment |
|------------|-----------|
| < 10% | Conservative target, suitable for standard sensorless FOC |
| 10–20% | Attemptable, needs Vdc feedforward, real-time sampling, power limiting, observer tuning |
| 20–30% | High risk. Angle estimation ripple or current loop saturation under accel/decel/load disturbance |
| > 30% | Not recommended as stable bus for standard sensorless FOC. Only if control strategy explicitly designed for large-ripple bus |

**Critical insight**: Minimum bus voltage matters more:
$$V_{dc,min} = V_{dc,avg} - \Delta V_{pp}/2$$

If Vdc_min drops below what's needed for the required back-EMF at current speed, SMO robustness is moot — current loop hits voltage saturation first.

## Summary Verdicts

```yaml
passive_single_phase_22uF_360W:
  verdict: infeasible_for_stable_dc_link

three_phase_22uF_360W:
  verdict: still_large_ripple_but_less_bad

pump_power_cube_model:
  verdict: valid_first_order_model
  refinement: add P0 offset term, P_avg_ref = P0 + k·ω³

20dB_APD:
  verdict: possible_but_requires_real_energy_buffer

smo_ripple_tolerance:
  verdict: context_dependent
  conservative_target: 10%pp
  assessment_at_18%pp: feasible_with_real_time_vdc_feedforward
```
