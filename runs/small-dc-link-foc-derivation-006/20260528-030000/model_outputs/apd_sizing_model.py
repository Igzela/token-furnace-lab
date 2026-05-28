"""
derivation-006: APD Hardware Sizing Model

Sweeps APD hardware parameters to find feasible component combinations.
Outputs: inductor size, MOSFET ratings, capacitor requirements, losses.
"""

import math
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class APDParams:
    Pavg: float = 300.0
    D_apd: float = 0.95
    Vdc_nom: float = 300.0
    Vdc_max: float = 400.0
    Vapd_min: float = 250.0
    Vapd_max: float = 450.0
    f_grid: float = 50.0

    @property
    def Vapd_center(self):
        return math.sqrt((self.Vapd_min**2 + self.Vapd_max**2) / 2.0)

    @property
    def P_apd_peak(self):
        return self.D_apd * self.Pavg


@dataclass
class SweepPoint:
    f_sw_khz: float = 40.0
    delta_I_pp: float = 0.4
    VL_max: float = 150.0
    Capd_uF: float = 22.0
    MOSFET_Rds_on: float = 0.45
    MOSFET_tr_ns: float = 30.0
    MOSFET_tf_ns: float = 30.0

    @property
    def f_sw(self):
        return self.f_sw_khz * 1e3

    @property
    def L_min_mH(self):
        if self.delta_I_pp <= 0:
            return float('inf')
        return self.VL_max / (2.0 * self.delta_I_pp * self.f_sw) * 1e3

    def compute_currents(self, apd: APDParams):
        I_lf_peak = apd.P_apd_peak / apd.Vapd_min
        I_lf_rms = apd.P_apd_peak / (math.sqrt(2) * apd.Vapd_center)
        I_lf_rms_upper = apd.P_apd_peak / (math.sqrt(2) * apd.Vapd_min)

        I_ripple_rms = self.delta_I_pp / math.sqrt(12)
        I_L_rms = math.sqrt(I_lf_rms**2 + I_ripple_rms**2)
        I_L_peak = I_lf_peak + self.delta_I_pp / 2.0

        return {
            'I_lf_peak': I_lf_peak,
            'I_lf_rms': I_lf_rms,
            'I_lf_rms_upper': I_lf_rms_upper,
            'I_ripple_rms': I_ripple_rms,
            'I_L_rms': I_L_rms,
            'I_L_peak': I_L_peak,
        }

    def compute_capacitor_current(self, apd: APDParams, k_ripple=0.5):
        I_lf_rms = apd.P_apd_peak / (math.sqrt(2) * apd.Vapd_center)
        I_C_ripple_rms = k_ripple * self.delta_I_pp / math.sqrt(12)
        I_C_rms = math.sqrt(I_lf_rms**2 + I_C_ripple_rms**2)
        return {
            'I_C_lf_rms': I_lf_rms,
            'I_C_ripple_rms': I_C_ripple_rms,
            'I_C_rms': I_C_rms,
        }

    def compute_mosfet_stress(self, apd: APDParams):
        Vds_case_a = max(apd.Vdc_max, apd.Vapd_max)
        Vds_case_b = apd.Vdc_max + apd.Vapd_max

        Vds_stress = Vds_case_a  # Unipolar switching

        if Vds_case_a <= 650:
            mosfet_voltage_rating = 650
        elif Vds_case_a <= 900:
            mosfet_voltage_rating = 900
        else:
            mosfet_voltage_rating = 1200

        return {
            'Vds_case_a': Vds_case_a,
            'Vds_case_b': Vds_case_b,
            'Vds_stress': Vds_stress,
            'mosfet_voltage_rating': mosfet_voltage_rating,
        }

    def compute_losses(self, apd: APDParams, currents: dict):
        I_rms = currents['I_L_rms']
        I_peak = currents['I_L_peak']
        Vds = max(apd.Vdc_max, apd.Vapd_max)
        tr = self.MOSFET_tr_ns * 1e-9
        tf = self.MOSFET_tf_ns * 1e-9

        P_cond_per_fet = I_rms**2 * self.MOSFET_Rds_on * 0.5
        P_cond_total = 4 * P_cond_per_fet

        P_sw_per_fet = 0.5 * Vds * I_peak * (tr + tf) * self.f_sw
        P_sw_total = 4 * P_sw_per_fet

        P_apd_total = P_cond_total + P_sw_total

        deadtime_error = 2 * 300e-9 * self.f_sw  # 300ns deadtime

        return {
            'P_cond_per_fet': P_cond_per_fet,
            'P_cond_total': P_cond_total,
            'P_sw_per_fet': P_sw_per_fet,
            'P_sw_total': P_sw_total,
            'P_apd_total': P_apd_total,
            'P_apd_pct': P_apd_total / apd.Pavg * 100,
            'deadtime_error_pct': deadtime_error * 100,
        }


def run_sweep():
    apd = APDParams()

    results = []
    for f_sw_khz in [20, 30, 40, 60]:
        for delta_I_pp in [0.2, 0.3, 0.4, 0.5, 0.8]:
            for VL_max in [100, 150, 200, 300]:
                for Capd_uF in [16, 22]:
                    sp = SweepPoint(
                        f_sw_khz=f_sw_khz,
                        delta_I_pp=delta_I_pp,
                        VL_max=VL_max,
                        Capd_uF=Capd_uF,
                    )
                    currents = sp.compute_currents(apd)
                    cap_currents = sp.compute_capacitor_current(apd)
                    mosfet = sp.compute_mosfet_stress(apd)
                    losses = sp.compute_losses(apd, currents)

                    # Pass/fail criteria
                    passed = True
                    reasons = []

                    if sp.L_min_mH > 15:
                        passed = False
                        reasons.append(f"L={sp.L_min_mH:.1f}mH too large")
                    if currents['I_L_peak'] > 3.0:
                        passed = False
                        reasons.append(f"I_peak={currents['I_L_peak']:.2f}A > 3A")
                    if losses['P_apd_pct'] > 5.0:
                        passed = False
                        reasons.append(f"Loss={losses['P_apd_pct']:.1f}% > 5%")
                    if losses['deadtime_error_pct'] > 3.0:
                        passed = False
                        reasons.append(f"DT error={losses['deadtime_error_pct']:.1f}% > 3%")

                    results.append({
                        'f_sw_khz': f_sw_khz,
                        'delta_I_pp': delta_I_pp,
                        'VL_max': VL_max,
                        'Capd_uF': Capd_uF,
                        'L_min_mH': round(sp.L_min_mH, 2),
                        'I_L_peak': round(currents['I_L_peak'], 3),
                        'I_L_rms': round(currents['I_L_rms'], 3),
                        'I_C_rms': round(cap_currents['I_C_rms'], 3),
                        'Vds_stress': mosfet['Vds_stress'],
                        'mosfet_v_rating': mosfet['mosfet_voltage_rating'],
                        'P_apd_total_W': round(losses['P_apd_total'], 3),
                        'P_apd_pct': round(losses['P_apd_pct'], 2),
                        'dt_error_pct': round(losses['deadtime_error_pct'], 2),
                        'passed': passed,
                        'reasons': reasons,
                    })

    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    print(f"Sweep: {passed}/{total} passed ({passed/total*100:.1f}%)")

    return results


def generate_report(results):
    lines = ["# derivation-006: APD Hardware Sizing Results\n"]

    passed = [r for r in results if r['passed']]
    failed = [r for r in results if not r['passed']]

    lines.append(f"Total: {len(results)} configs, {len(passed)} passed ({len(passed)/len(results)*100:.1f}%)\n")

    # Best configs (lowest L with pass)
    lines.append("## Best Configs (Lowest Inductance, Pass)\n")
    lines.append("| f_sw | ΔI_pp | VL_max | Capd | L_min | I_peak | I_rms | Vds | MOSFET | Loss | DT err |")
    lines.append("|------|-------|--------|------|-------|--------|-------|-----|--------|------|--------|")
    best = sorted(passed, key=lambda r: r['L_min_mH'])
    for r in best[:20]:
        lines.append(
            f"| {r['f_sw_khz']}kHz | {r['delta_I_pp']}A | {r['VL_max']}V | "
            f"{r['Capd_uF']}µF | {r['L_min_mH']}mH | {r['I_L_peak']}A | "
            f"{r['I_L_rms']}A | {r['Vds_stress']}V | {r['mosfet_v_rating']}V | "
            f"{r['P_apd_total_W']}W | {r['dt_error_pct']}% |"
        )

    # Failure breakdown
    lines.append("\n## Failure Breakdown\n")
    rc = {}
    for r in failed:
        for reason in r['reasons']:
            k = reason.split()[0]
            rc[k] = rc.get(k, 0) + 1
    for k, v in sorted(rc.items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")

    # Recommended baseline
    lines.append("\n## Recommended APD Hardware Baseline\n")
    if best:
        b = best[0]
        lines.append(f"- Inductor: {b['L_min_mH']}mH / ≥3A sat / ≥1A RMS")
        lines.append(f"- Capacitor: {b['Capd_uF']}µF / 500V film / ≥1A RMS")
        lines.append(f"- MOSFETs: {b['mosfet_v_rating']}V / ≥5A / Rds_on < 1Ω")
        lines.append(f"- Switching freq: {b['f_sw_khz']}kHz")
        lines.append(f"- APD loss: {b['P_apd_total_W']}W ({b['P_apd_pct']}%)")

    return "\n".join(lines)


if __name__ == "__main__":
    out_dir = Path(__file__).parent

    results = run_sweep()

    report = generate_report(results)
    (out_dir / "sizing_results.md").write_text(report)

    (out_dir / "sizing_raw.json").write_text(json.dumps(results, indent=2))

    print(f"\nSaved to {out_dir}")

    # Print recommended baseline
    passed = [r for r in results if r['passed']]
    if passed:
        best = min(passed, key=lambda r: r['L_min_mH'])
        print(f"\nRecommended: L={best['L_min_mH']}mH, f_sw={best['f_sw_khz']}kHz, "
              f"MOSFET={best['mosfet_v_rating']}V, Loss={best['P_apd_total_W']}W")
