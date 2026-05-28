"""
Phase C-001: DC-Link Voltage Ripple Management Simulation

Models 22µF DC-link ripple, APD decoupling, Vdc feedforward,
IqLimiter, and SVPWM saturation for sensorless FOC drive.
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
    omega_m_rated: float = 418.9

    @property
    def Kt(self) -> float:
        return 1.5 * self.p * self.psi_f


@dataclass
class DcLinkParams:
    Cdc: float = 22e-6
    Vdc_nom: float = 300.0
    f_line: float = 50.0
    Vapd_nom: float = 364.0


@dataclass
class APDParams:
    C_apd: float = 22e-6
    V_apd_rated: float = 500.0
    K_decouple: float = 0.9
    f_sw: float = 40000.0


@dataclass
class SMOParams:
    k_gain: float = 145.0
    LPF_cutoff: float = 2000.0
    tau_obs: float = 0.001


@dataclass
class ControlParams:
    Kp_speed: float = 0.004
    Ki_speed: float = 2.0
    Kp_current: float = 120.54
    Ki_current: float = 70440.0
    Iq_max_margin: float = 0.9
    overmodulation_boost: float = 0.15


def simulate_dc_link(motor: MotorParams, dc: DcLinkParams,
                     apd: APDParams, smo: SMOParams,
                     ctrl: ControlParams, T_load: float = 0.5,
                     omega_ref: float = 300.0) -> dict:
    """Simulate one period of DC-link ripple with APD decoupling."""
    Ts = 1e-5  # 100µs ISR
    T_sim = 0.1  # 100ms (5 full line cycles)
    steps = int(T_sim / Ts)
    omega_line = 2 * math.pi * dc.f_line

    # State variables
    Vdc = dc.Vdc_nom
    E_cap = 0.5 * dc.Cdc * Vdc**2
    omega_m = 0.0
    omega_e = omega_m * motor.p / 2
    theta_e = 0.0
    theta_obs = 0.0

    # PI state
    speed_int = 0.0
    Id_int = 0.0
    Iq_int = 0.0

    # APD state
    E_apd = 0.5 * apd.C_apd * dc.Vapd_nom**2
    P_avg_ref = 0.0
    P_apd = 0.0

    history = {
        't': [], 'Vdc': [], 'Vdc_ripple': [], 'omega_m': [],
        'Iq_ref': [], 'Iq_meas': [], 'Id_ref': [],
        'theta_err_deg': [], 'P_motor': [], 'P_apd': [],
        'Vapd': [], 'Iq_max': [], 'svpwm_sat': [],
    }

    for step in range(steps):
        t = step * Ts

        # === DC-LINK VOLTAGE MODEL ===
        # Motor power
        P_motor = T_load * omega_m
        P_loss = 3 * (ctrl.Iq_max_margin * motor.I_rated)**2 * motor.Rs * 0.1
        P_input = P_motor + P_loss

        # Pavg_ref for APD (GPT corrected: P0 + k*omega^3)
        P_avg_ref = 5.0 + 4.07e-6 * omega_m**3

        # APD absorbs power fluctuation (reduces ripple on main cap)
        # Power fluctuation seen by main cap = P_input - P_avg_ref
        P_fluct = P_input - P_avg_ref
        P_fluct_after_apd = P_fluct * (1 - apd.K_decouple)

        # Voltage ripple from energy balance (corrected model)
        # dE = P_fluct_after_apd * dt → dV = P_fluct_after_apd / (Vdc * omega_line * Cdc)
        if Vdc > 50:
            Vdc_ripple = P_fluct_after_apd / (Vdc * omega_line * dc.Cdc)
        else:
            Vdc_ripple = 0
        Vdc_ripple *= math.sin(2 * omega_line * t)

        # APD capacitor energy
        P_apd = apd.K_decouple * P_fluct * math.sin(2 * omega_line * t)

        # Energy balance on main cap
        dE = P_fluct_after_apd * Ts
        E_cap -= dE
        E_cap = max(E_cap, 0.5 * dc.Cdc * (dc.Vdc_nom * 0.3)**2)
        E_cap = min(E_cap, 0.5 * dc.Cdc * (dc.Vdc_nom * 1.3)**2)
        Vdc = math.sqrt(2 * E_cap / dc.Cdc)

        # APD capacitor
        E_apd += P_apd * Ts
        E_apd = max(0, 0.5 * apd.C_apd * 100**2)
        E_apd = min(E_apd, 0.5 * apd.C_apd * apd.V_apd_rated**2)
        Vapd = math.sqrt(2 * E_apd / apd.C_apd) if E_apd > 0 else dc.Vapd_nom

        # === SPEED PI ===
        speed_error = omega_ref - omega_m
        speed_int += ctrl.Ki_speed * speed_error * Ts
        speed_int = max(-motor.I_rated, min(motor.I_rated, speed_int))
        Iq_cmd = ctrl.Kp_speed * speed_error + speed_int

        # === IqLimiter (Vdc-aware) ===
        omega_e_abs = abs(omega_e) if abs(omega_e) > 1 else 1
        Vdc_min = Vdc * (1 - Vdc_ripple / dc.Vdc_nom) if Vdc > 50 else dc.Vdc_nom * 0.5
        Vdc_min = max(Vdc_min, dc.Vdc_nom * 0.5)
        V_available = Vdc_min / math.sqrt(3)
        V_backemf = motor.psi_f * omega_e_abs
        V_margin = max(V_available - V_backemf, 0)
        Iq_max = V_margin / (omega_e_abs * motor.Ls) if omega_e_abs > 10 else motor.I_rated
        Iq_max = min(Iq_max, motor.I_rated) * ctrl.Iq_max_margin

        Iq_ref = max(-Iq_max, min(Iq_max, Iq_cmd))
        Id_ref = 0.0

        # === SVPWM SATURATION CHECK ===
        V_req = math.sqrt((Id_ref * omega_e_abs * motor.Ls)**2 +
                          (Iq_ref * omega_e_abs * motor.Ls + motor.psi_f * omega_e_abs)**2)
        V_max_svpwm = Vdc / math.sqrt(3) * (1 + ctrl.overmodulation_boost)
        svpwm_saturated = V_req > V_max_svpwm

        # === CURRENT PI (simplified) ===
        Iq_meas = Iq_ref * (0.95 + 0.05 * math.sin(100 * t))  # simplified dynamics
        Id_meas = Id_ref

        # === SPEED DYNAMICS ===
        torque = motor.Kt * Iq_meas
        alpha_m = (torque - T_load) / 1e-4  # J = 1e-4
        omega_m += alpha_m * Ts
        omega_m = max(0, omega_m)
        omega_e = omega_m * motor.p / 2
        theta_e += omega_e * Ts

        # === SMO OBSERVER (simplified) ===
        E_bemf = motor.psi_f * omega_e
        if abs(E_bemf) > 0.1:
            theta_err = (smo.k_gain * (Iq_meas - motor.psi_f * omega_e /
                        (motor.Ls * omega_e)) * motor.Ls / E_bemf
                        if omega_e > 1 else 0.5)
            theta_obs = theta_obs + (theta_e + theta_err * 0.3 - theta_obs) * min(1.0, Ts / smo.tau_obs)
        else:
            theta_obs = theta_e

        theta_err_deg = abs(theta_e - theta_obs) * 180 / math.pi
        if theta_err_deg > 180:
            theta_err_deg = 360 - theta_err_deg

        # Record every 100th sample
        if step % 100 == 0:
            history['t'].append(t)
            history['Vdc'].append(Vdc)
            history['Vdc_ripple'].append(Vdc_ripple)
            history['omega_m'].append(omega_m)
            history['Iq_ref'].append(Iq_ref)
            history['Iq_meas'].append(Iq_meas)
            history['Id_ref'].append(Id_ref)
            history['theta_err_deg'].append(theta_err_deg)
            history['P_motor'].append(P_motor)
            history['P_apd'].append(P_apd)
            history['Vapd'].append(Vapd)
            history['Iq_max'].append(Iq_max)
            history['svpwm_sat'].append(1 if svpwm_saturated else 0)

    # Analysis
    Vdc_values = history['Vdc']
    Vdc_min = min(Vdc_values)
    Vdc_max = max(Vdc_values)
    Vdc_avg = sum(Vdc_values) / len(Vdc_values)
    ripple_pp = Vdc_max - Vdc_min
    ripple_pct = ripple_pp / Vdc_avg * 100 if Vdc_avg > 0 else 0

    max_theta_err = max(history['theta_err_deg'])
    max_Iq = max(abs(x) for x in history['Iq_ref'])
    sat_count = sum(history['svpwm_sat'])
    sat_pct = sat_count / len(history['svpwm_sat']) * 100

    return {
        'Vdc_min': round(Vdc_min, 1),
        'Vdc_max': round(Vdc_max, 1),
        'Vdc_avg': round(Vdc_avg, 1),
        'ripple_V': round(ripple_pp, 1),
        'ripple_pct': round(ripple_pct, 2),
        'max_theta_err_deg': round(max_theta_err, 2),
        'max_Iq_A': round(max_Iq, 2),
        'svpwm_sat_pct': round(sat_pct, 2),
        'K_apd': apd.K_decouple,
        'Cdc_uF': dc.Cdc * 1e6,
    }


def run_sweep():
    results = []
    for Cdc in [22e-6, 47e-6, 100e-6]:
        for K_apd in [0.0, 0.5, 0.9, 0.95]:
            for T_load in [0.1, 0.5, 1.0, 1.44]:
                for omega_ref in [100, 200, 300, 400]:
                    motor = MotorParams()
                    dc = DcLinkParams(Cdc=Cdc)
                    apd = APDParams(K_decouple=K_apd)
                    smo = SMOParams()
                    ctrl = ControlParams()

                    result = simulate_dc_link(motor, dc, apd, smo, ctrl,
                                              T_load=T_load, omega_ref=omega_ref)

                    # Pass criteria
                    passed = True
                    reasons = []
                    if result['ripple_pct'] > 10:
                        passed = False
                        reasons.append(f"ripple={result['ripple_pct']:.1f}%>10%")
                    if result['Vdc_min'] < 200:
                        passed = False
                        reasons.append(f"Vdc_min={result['Vdc_min']:.0f}V<200V")
                    if result['max_theta_err_deg'] > 30:
                        passed = False
                        reasons.append(f"theta_err={result['max_theta_err_deg']:.1f}°>30°")
                    if result['svpwm_sat_pct'] > 5:
                        passed = False
                        reasons.append(f"svpwm_sat={result['svpwm_sat_pct']:.1f}%>5%")

                    P_rated = motor.Kt * T_load * omega_ref
                    results.append({
                        'Cdc_uF': Cdc * 1e6,
                        'K_apd': K_apd,
                        'T_load': T_load,
                        'omega_ref': omega_ref,
                        'P_rated_W': round(P_rated, 1),
                        'passed': passed,
                        'reasons': reasons,
                        **result,
                    })

    total = len(results)
    passed_count = sum(1 for r in results if r['passed'])
    print(f"Sweep: {passed_count}/{total} passed ({passed_count/total*100:.1f}%)")
    return results


def generate_report(results):
    lines = ["# Phase C-001: DC-Link Ripple Management Results\n"]
    lines.append("22µF DC-link + APD decoupling + Vdc feedforward + IqLimiter\n")

    passed = [r for r in results if r['passed']]
    failed = [r for r in results if not r['passed']]

    lines.append(f"Total: {len(results)} configs, {len(passed)} passed ({len(passed)/len(results)*100:.1f}%)\n")

    lines.append("## Best Configs (Lowest Ripple, Pass)\n")
    lines.append("| Cdc(µF) | K_apd | T_load(Nm) | ω_ref(rad/s) | P(W) | Vdc_min(V) | Ripple(%) | θ_err(°) | SVPWM_sat(%) |")
    lines.append("|---------|-------|------------|--------------|------|------------|-----------|----------|--------------|")
    best = sorted(passed, key=lambda r: r['ripple_pct'])
    for r in best[:15]:
        lines.append(
            f"| {r['Cdc_uF']} | {r['K_apd']} | {r['T_load']} | "
            f"{r['omega_ref']} | {r['P_rated_W']} | {r['Vdc_min']} | "
            f"{r['ripple_pct']} | {r['max_theta_err_deg']} | {r['svpwm_sat_pct']} |"
        )

    lines.append("\n## Failure Breakdown\n")
    rc = {}
    for r in failed:
        for reason in r['reasons']:
            k = reason.split('=')[0] if '=' in reason else reason
            rc[k] = rc.get(k, 0) + 1
    for k, v in sorted(rc.items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")

    lines.append("\n## Recommended Baseline\n")
    if best:
        b = best[0]
        lines.append(f"- Cdc: {b['Cdc_uF']}µF")
        lines.append(f"- K_apd: {b['K_apd']} ({b['K_apd']*100:.0f}% decoupling)")
        lines.append(f"- Ripple: {b['ripple_pct']}%pp")
        lines.append(f"- Vdc_min: {b['Vdc_min']}V")
        lines.append(f"- Max θ error: {b['max_theta_err_deg']}°")
        lines.append(f"- SVPWM saturation: {b['svpwm_sat_pct']}%")

    return "\n".join(lines)


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    results = run_sweep()
    report = generate_report(results)
    (out_dir / "sweep_results.md").write_text(report)
    (out_dir / "sweep_raw.json").write_text(json.dumps(results, indent=2))
    print(f"\nSaved to {out_dir}")
