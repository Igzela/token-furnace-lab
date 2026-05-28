"""
Phase C-003: APD and Capacitance Margin Characterization

Quantifies design margin for 22µF DC-link + APD under component
tolerances and operating variations. Not feasibility proof —
margin characterization for hardware confidence.
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


def simulate_margin(Cdc: float, K_apd: float, Cdc_tol: float,
                    Vline_factor: float, T_load: float,
                    omega_ref: float) -> dict:
    """Simulate ripple with margin parameters."""
    Ts = 1e-5
    T_sim = 0.1
    steps = int(T_sim / Ts)
    Vdc_nom = 300.0 * Vline_factor
    f_line = 50.0
    omega_ripple = 2 * math.pi * 100  # single-phase 100Hz

    Cdc_eff = Cdc * Cdc_tol  # tolerance factor
    motor = MotorParams()

    Vdc = Vdc_nom
    E_cap = 0.5 * Cdc_eff * Vdc**2
    omega_m = omega_ref * 0.8

    Vdc_min = Vdc
    Vdc_max = Vdc
    Vdc_sum = 0.0
    count = 0

    for step in range(steps):
        t = step * Ts
        P_motor = T_load * omega_m
        P_loss = 3 * (motor.I_rated * 0.9)**2 * motor.Rs * 0.1
        P_input = P_motor + P_loss
        P_avg_ref = 5.0 + 4.07e-6 * omega_m**3
        P_fluct = P_input - P_avg_ref
        P_fluct_after_apd = P_fluct * (1 - K_apd)

        if Vdc > 50:
            dE = P_fluct_after_apd * math.sin(omega_ripple * t) * Ts
        else:
            dE = 0
        E_cap -= dE
        E_cap = max(E_cap, 0.5 * Cdc_eff * (Vdc_nom * 0.3)**2)
        E_cap = min(E_cap, 0.5 * Cdc_eff * (Vdc_nom * 1.3)**2)
        Vdc = math.sqrt(2 * E_cap / Cdc_eff) if E_cap > 0 else Vdc_nom

        Vdc_min = min(Vdc_min, Vdc)
        Vdc_max = max(Vdc_max, Vdc)
        Vdc_sum += Vdc
        count += 1

    Vdc_avg = Vdc_sum / count if count > 0 else Vdc_nom
    ripple_pp = Vdc_max - Vdc_min
    ripple_pct = ripple_pp / Vdc_avg * 100 if Vdc_avg > 0 else 0

    passed = ripple_pct <= 10 and Vdc_min >= 200
    return {
        'Cdc_uF': Cdc * 1e6,
        'K_apd': K_apd,
        'Cdc_tol': Cdc_tol,
        'Vline_factor': Vline_factor,
        'T_load': T_load,
        'omega_ref': omega_ref,
        'ripple_pct': round(ripple_pct, 2),
        'Vdc_min': round(Vdc_min, 1),
        'passed': passed,
    }


def run_sweep():
    results = []
    for Cdc in [15e-6, 18e-6, 22e-6, 33e-6, 47e-6]:
        for K_apd in [0.80, 0.85, 0.90, 0.95]:
            for Cdc_tol in [1.0, 0.9, 0.8]:  # nominal, -10%, -20%
                for Vline_factor in [0.9, 1.0, 1.1]:  # low, nominal, high
                    for T_load in [0.1, 0.5, 1.0, 1.44]:
                        for omega_ref in [100, 200, 300, 400]:
                            result = simulate_margin(
                                Cdc, K_apd, Cdc_tol, Vline_factor,
                                T_load, omega_ref)
                            results.append(result)

    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    print(f"Sweep: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return results


def generate_report(results):
    lines = ["# Phase C-003: APD and Capacitance Margin Characterization\n"]
    lines.append("Design margin for 22µF DC-link under component tolerances\n")

    # Pass rate by key parameters
    lines.append("## Pass Rate by Cdc and K_apd\n")
    lines.append("| Cdc(µF) | K_apd=0.80 | K_apd=0.85 | K_apd=0.90 | K_apd=0.95 |")
    lines.append("|---------|------------|------------|------------|------------|")
    for Cdc in [15, 18, 22, 33, 47]:
        row = [f"| {Cdc}"]
        for K_apd in [0.80, 0.85, 0.90, 0.95]:
            subset = [r for r in results if r['Cdc_uF'] == Cdc and r['K_apd'] == K_apd]
            p = sum(1 for r in subset if r['passed'])
            t = len(subset)
            row.append(f"{p}/{t} ({p/t*100:.0f}%)")
        lines.append(" | ".join(row) + " |")

    # Worst-case margin at 22µF
    lines.append("\n## 22µF Worst-Case Margin\n")
    lines.append("| K_apd | Cdc_tol | Vline | Pass Rate |")
    lines.append("|-------|---------|-------|-----------|")
    for K_apd in [0.80, 0.85, 0.90, 0.95]:
        for Cdc_tol in [1.0, 0.9, 0.8]:
            for Vline in [0.9, 1.0, 1.1]:
                subset = [r for r in results
                         if r['Cdc_uF'] == 22.0 and r['K_apd'] == K_apd
                         and r['Cdc_tol'] == Cdc_tol and r['Vline_factor'] == Vline]
                p = sum(1 for r in subset if r['passed'])
                t = len(subset)
                lines.append(f"| {K_apd} | {Cdc_tol} | {Vline} | {p}/{t} ({p/t*100:.0f}%) |")

    # Minimum safe operating point
    passed = [r for r in results if r['passed']]
    lines.append(f"\n## Total: {len(passed)}/{len(results)} passed ({len(passed)/len(results)*100:.1f}%)\n")

    # Find minimum Cdc that passes at 90% APD with worst-case tolerance
    for K_apd in [0.80, 0.85, 0.90, 0.95]:
        worst = [r for r in results if r['K_apd'] == K_apd
                and r['Cdc_tol'] == 0.8 and r['Vline_factor'] == 0.9]
        p = sum(1 for r in worst if r['passed'])
        t = len(worst)
        min_cdc = None
        for Cdc in [15, 18, 22, 33, 47]:
            sub = [r for r in worst if r['Cdc_uF'] == Cdc]
            if all(r['passed'] for r in sub) and len(sub) > 0:
                min_cdc = Cdc
                break
        lines.append(f"- K_apd={K_apd}: worst-case pass {p}/{t}, min safe Cdc={min_cdc}µF")

    return "\n".join(lines)


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    results = run_sweep()
    report = generate_report(results)
    (out_dir / "sweep_results.md").write_text(report)
    (out_dir / "sweep_raw.json").write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out_dir}")
