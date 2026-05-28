"""
Phase C-002: Single-Phase vs Three-Phase Ripple Comparison

Compares DC-link ripple for 22µF capacitor under single-phase (100Hz)
and three-phase (300Hz) rectified input, with and without APD.
"""

import math
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MotorParams:
    p: int = 4
    Rs: float = 2.0
    Ls: float = 5e-3
    psi_f: float = 0.08
    I_rated: float = 3.0

    @property
    def Kt(self) -> float:
        return 1.5 * self.p * self.psi_f


@dataclass
class DcLinkParams:
    Cdc: float = 22e-6
    Vdc_nom: float = 300.0
    Vapd_nom: float = 364.0
    f_line: float = 50.0


@dataclass
class APDParams:
    C_apd: float = 22e-6
    V_apd_rated: float = 500.0
    K_decouple: float = 0.9


def simulate_ripple(motor: MotorParams, dc: DcLinkParams,
                    apd: APDParams, input_type: str,
                    T_load: float, omega_ref: float) -> dict:
    """Simulate DC-link ripple for given input type and load."""
    Ts = 1e-5
    T_sim = 0.1
    steps = int(T_sim / Ts)

    # Ripple frequency depends on input type
    if input_type == "single_phase":
        omega_ripple = 2 * math.pi * 2 * dc.f_line  # 100Hz
        ripple_amplitude_factor = 1.0
    else:  # three_phase
        omega_ripple = 2 * math.pi * 6 * dc.f_line  # 300Hz
        ripple_amplitude_factor = 0.33  # ~1/3 of single-phase

    Vdc = dc.Vdc_nom
    E_cap = 0.5 * dc.Cdc * Vdc**2
    omega_m = omega_ref * 0.8  # simplified speed
    E_apd = 0.5 * apd.C_apd * dc.Vapd_nom**2

    Vdc_min = Vdc
    Vdc_max = Vdc
    Vdc_sum = 0.0
    count = 0

    for step in range(steps):
        t = step * Ts

        # Motor power
        P_motor = T_load * omega_m
        P_loss = 3 * (motor.I_rated * 0.9)**2 * motor.Rs * 0.1
        P_input = P_motor + P_loss

        # Pavg_ref
        P_avg_ref = 5.0 + 4.07e-6 * omega_m**3

        # Power fluctuation (with ripple amplitude factor)
        P_fluct = (P_input - P_avg_ref) * ripple_amplitude_factor

        # APD decoupling
        P_fluct_after_apd = P_fluct * (1 - apd.K_decouple)

        # Voltage ripple
        if Vdc > 50:
            Vdc_ripple = P_fluct_after_apd / (Vdc * omega_ripple * dc.Cdc)
        else:
            Vdc_ripple = 0
        Vdc_ripple *= math.sin(omega_ripple * t)

        # Energy balance
        dE = P_fluct_after_apd * math.sin(omega_ripple * t) * Ts
        E_cap -= dE
        E_cap = max(E_cap, 0.5 * dc.Cdc * (dc.Vdc_nom * 0.3)**2)
        E_cap = min(E_cap, 0.5 * dc.Cdc * (dc.Vdc_nom * 1.3)**2)
        Vdc = math.sqrt(2 * E_cap / dc.Cdc)

        Vdc_min = min(Vdc_min, Vdc)
        Vdc_max = max(Vdc_max, Vdc)
        Vdc_sum += Vdc
        count += 1

    Vdc_avg = Vdc_sum / count if count > 0 else dc.Vdc_nom
    ripple_pp = Vdc_max - Vdc_min
    ripple_pct = ripple_pp / Vdc_avg * 100 if Vdc_avg > 0 else 0

    # Pass criteria
    passed = True
    reasons = []
    if ripple_pct > 10:
        passed = False
        reasons.append(f"ripple={ripple_pct:.1f}%>10%")
    if Vdc_min < 200:
        passed = False
        reasons.append(f"Vdc_min={Vdc_min:.0f}V<200V")

    return {
        'input_type': input_type,
        'K_apd': apd.K_decouple,
        'Cdc_uF': dc.Cdc * 1e6,
        'T_load': T_load,
        'omega_ref': omega_ref,
        'Vdc_min': round(Vdc_min, 1),
        'Vdc_max': round(Vdc_max, 1),
        'Vdc_avg': round(Vdc_avg, 1),
        'ripple_V': round(ripple_pp, 1),
        'ripple_pct': round(ripple_pct, 2),
        'passed': passed,
        'reasons': reasons,
    }


def run_sweep():
    motor = MotorParams()
    results = []

    for input_type in ["single_phase", "three_phase"]:
        for Cdc in [22e-6, 47e-6, 100e-6]:
            for K_apd in [0.0, 0.9, 0.95]:
                for T_load in [0.1, 0.5, 1.0, 1.44]:
                    for omega_ref in [100, 200, 300, 400]:
                        dc = DcLinkParams(Cdc=Cdc)
                        apd = APDParams(K_decouple=K_apd)
                        result = simulate_ripple(motor, dc, apd,
                                                 input_type, T_load, omega_ref)
                        results.append(result)

    total = len(results)
    passed_count = sum(1 for r in results if r['passed'])
    print(f"Sweep: {passed_count}/{total} passed ({passed_count/total*100:.1f}%)")
    return results


def generate_report(results):
    lines = ["# Phase C-002: Single-Phase vs Three-Phase Ripple Comparison\n"]
    lines.append("22µF DC-link, single-phase (100Hz) vs three-phase (300Hz) rectified input\n")

    # Summary by input type and K_apd
    lines.append("## Pass Rate by Input Type and APD\n")
    lines.append("| Input | K_apd | Cdc(µF) | Pass Rate |")
    lines.append("|-------|-------|---------|-----------|")
    for input_type in ["single_phase", "three_phase"]:
        for K_apd in [0.0, 0.9, 0.95]:
            for Cdc in [22, 47, 100]:
                subset = [r for r in results
                         if r['input_type'] == input_type
                         and r['K_apd'] == K_apd
                         and r['Cdc_uF'] == Cdc]
                passed = sum(1 for r in subset if r['passed'])
                total = len(subset)
                rate = passed / total * 100 if total > 0 else 0
                lines.append(f"| {input_type} | {K_apd} | {Cdc} | {passed}/{total} ({rate:.0f}%) |")

    # Best configs
    passed = [r for r in results if r['passed']]
    lines.append(f"\n## Total: {len(passed)}/{len(results)} passed ({len(passed)/len(results)*100:.1f}%)\n")

    lines.append("## Best Configs (Lowest Ripple, Pass)\n")
    lines.append("| Input | Cdc(µF) | K_apd | T_load | ω_ref | Ripple(%) | Vdc_min(V) |")
    lines.append("|-------|---------|-------|--------|-------|-----------|------------|")
    best = sorted(passed, key=lambda r: r['ripple_pct'])
    for r in best[:15]:
        lines.append(
            f"| {r['input_type']} | {r['Cdc_uF']} | {r['K_apd']} | "
            f"{r['T_load']} | {r['omega_ref']} | {r['ripple_pct']} | {r['Vdc_min']} |"
        )

    # Comparison at 22µF medium load
    lines.append("\n## 22µF Medium Load Comparison (T=0.5, ω=200)\n")
    lines.append("| Input | K_apd | Ripple(%) | Vdc_min(V) | Pass |")
    lines.append("|-------|-------|-----------|------------|------|")
    for r in results:
        if (r['Cdc_uF'] == 22.0 and r['T_load'] == 0.5
            and r['omega_ref'] == 200):
            lines.append(
                f"| {r['input_type']} | {r['K_apd']} | {r['ripple_pct']} | "
                f"{r['Vdc_min']} | {'PASS' if r['passed'] else 'FAIL'} |"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    results = run_sweep()
    report = generate_report(results)
    (out_dir / "sweep_results.md").write_text(report)
    (out_dir / "sweep_raw.json").write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out_dir}")
