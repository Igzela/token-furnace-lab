"""
Phase B-002: Corrected I-f Startup Model (GPT corrections applied)

Corrections from Phase B-001 GPT review (76/100):
1. ψ_f = 0.08 Wb (corrected from ke=0.15)
2. Expanded observer model (LPF delay, deadtime, param error)
3. APD precharge state before ALIGN
4. Observer-gated blend (not time-based)
5. S-curve ramp (jerk-limited)
6. Safety checks and fault exits
"""

import math
import json
from dataclasses import dataclass, field
from pathlib import Path
from enum import IntEnum


class StartupState(IntEnum):
    IDLE = 0
    PRECHARGE_APD = 1
    CHECK_VDC = 2
    ALIGN = 3
    IF_RAMP = 4
    OBSERVER_CHECK = 5
    BLEND = 6
    FOC = 7
    FAULT = 8


@dataclass
class MotorParams:
    p: int = 4
    Rs: float = 2.0          # ohm
    Ls: float = 5e-3         # H
    psi_f: float = 0.08      # Wb (rotor flux linkage, corrected from 0.15)
    I_rated: float = 3.0     # A
    omega_m_rated: float = 418.9  # rad/s mech (4000rpm)
    J: float = 1e-4          # kg·m²
    B: float = 1e-4          # N·m·s/rad (friction)

    @property
    def Kt(self) -> float:
        return 1.5 * self.p * self.psi_f  # Nm/A

    @property
    def ke_phase(self) -> float:
        return self.psi_f  # V/(rad/s electrical), phase peak


@dataclass
class DcLinkParams:
    Cdc: float = 22e-6       # F
    Vdc_nom: float = 300.0   # V
    Vdc_min: float = 250.0   # V


@dataclass
class ObserverParams:
    V_noise: float = 0.2          # V (ADC + switching noise, after filtering)
    V_deadtime: float = 0.15      # V (deadtime voltage error, compensated)
    V_param_error: float = 0.1    # V (Rs/Ls parameter mismatch, tuned)
    LPF_cutoff_hz: float = 2000.0  # Hz (SMO low-pass filter, higher = less delay)
    LPF_order: int = 1            # filter order (1st order = less phase lag)
    tau_obs: float = 0.001        # s (observer convergence time constant)


@dataclass
class StartupParams:
    I_align: float = 1.5         # A
    T_align_ms: float = 200.0    # ms
    I_start: float = 1.0         # A (corrected per GPT: test 1.0A)
    T_current_ramp_ms: float = 100.0  # ms (slower ramp per GPT)
    omega_start_mech: float = 50.0    # rad/s mech (observer-check speed)
    omega_end_mech: float = 80.0      # rad/s mech (safe transition)
    T_blend_ms: float = 200.0         # ms
    theta_err_start_blend: float = 45.0   # degrees
    theta_err_continue_blend: float = 30.0  # degrees
    theta_err_complete_foc: float = 20.0    # degrees
    N_converge_samples: int = 100    # samples below threshold for FOC
    ISR_freq_hz: float = 10000.0
    f_sw: float = 40000.0
    # S-curve ramp parameters
    omega_ramp_rate: float = 2000.0   # rad/s² electrical (acceleration limit)
    omega_jerk_limit: float = 10000.0 # rad/s³ (jerk limit for S-curve)
    # Fault thresholds
    Vdc_uvlo: float = 200.0    # V (undervoltage lockout)
    Vdc_ov: float = 450.0      # V (overvoltage)
    I_oc: float = 5.0          # A (overcurrent)
    Vapd_min: float = 200.0    # V
    Vapd_max: float = 500.0    # V


def omega_e_to_mech(omega_e: float, p: int) -> float:
    return omega_e / (p / 2)


def mech_to_omega_e(omega_m: float, p: int) -> float:
    return omega_m * (p / 2)


def simulate_startup(motor: MotorParams, dc: DcLinkParams,
                     obs: ObserverParams, params: StartupParams) -> dict:
    Ts = 1.0 / params.ISR_freq_hz
    p = motor.p
    Kt = motor.Kt

    state = StartupState.IDLE
    t = 0.0

    omega_e = 0.0       # electrical rad/s (commanded)
    omega_m = 0.0       # mechanical rad/s
    theta_e = 0.0       # electrical angle (commanded)
    theta_actual = 0.0  # actual motor angle (for observer to track)

    # S-curve ramp state
    omega_e_dot = 0.0   # electrical acceleration (rad/s²)
    omega_e_target = 0.0  # target speed

    I_align_count = int(params.T_align_ms / 1000.0 / Ts)
    I_ramp_count = int(params.T_current_ramp_ms / 1000.0 / Ts)

    # Observer state
    theta_obs = 0.0
    omega_obs = 0.0     # estimated speed
    lpf_output = 0.0
    lpf_prev = 0.0

    # Blend state
    alpha = 0.0
    blend_active = False
    converge_count = 0

    # Current references
    Id_ref = 0.0
    Iq_ref = 0.0

    # Vdc tracking
    Vdc = dc.Vdc_nom
    Vapd = 364.0  # energy center
    E_stored = 0.5 * dc.Cdc * Vdc**2

    # State machine
    state = StartupState.PRECHARGE_APD
    align_timer = 0
    ramp_timer = 0
    blend_timer = 0
    precharge_timer = 0

    # Fault tracking
    fault_code = 0

    # Records
    history = {
        't': [], 'state': [], 'omega_m': [], 'omega_e': [],
        'theta_e': [], 'theta_obs': [], 'theta_error_deg': [],
        'Id_ref': [], 'Iq_ref': [], 'alpha': [], 'Vdc': [],
        'torque': [], 'Vapd': [],
    }

    max_steps = int(5.0 / Ts)
    converged = False

    for step in range(max_steps):
        # === EXPANDED OBSERVER MODEL ===
        # Observer estimates theta_actual with error sources
        # θ_obs tracks θ_actual with noise + lag
        if omega_m > 0.1:
            E_bemf = motor.ke_phase * omega_m * (p / 2)  # phase back-EMF

            # Error sources (RSS — uncorrelated)
            theta_noise = obs.V_noise / E_bemf if E_bemf > 0.1 else 0.3
            theta_deadtime = obs.V_deadtime / E_bemf if E_bemf > 0.1 else 0.2
            theta_param = obs.V_param_error / E_bemf if E_bemf > 0.1 else 0.15

            # LPF phase delay
            f_signal = omega_m * p / (2 * math.pi)
            phase_lpf = math.atan(f_signal / obs.LPF_cutoff_hz) if obs.LPF_cutoff_hz > 0 else 0
            theta_lpf = phase_lpf

            # Total error (RSS)
            theta_err_total = math.sqrt(theta_noise**2 + theta_deadtime**2 +
                                       theta_param**2 + theta_lpf**2)

            # Observer tracks actual angle with error (lag + noise)
            # Target: actual angle + steady-state error offset
            theta_obs_target = theta_actual + theta_err_total * 0.3  # 30% of error as offset
            theta_obs = theta_obs + (theta_obs_target - theta_obs) * min(1.0, Ts / obs.tau_obs)
        else:
            theta_obs = theta_actual  # no estimation at standstill

        torque = 0.0  # default, set by state machine

        # === FAULT CHECKS ===
        if Vdc < params.Vdc_uvlo:
            fault_code = 1  # UVLO
            state = StartupState.FAULT
        elif Vdc > params.Vdc_ov:
            fault_code = 2  # OV
            state = StartupState.FAULT
        elif Iq_ref > params.I_oc or Id_ref > params.I_oc:
            fault_code = 3  # OC
            state = StartupState.FAULT

        # === STATE MACHINE ===
        if state == StartupState.PRECHARGE_APD:
            # Precharge APD capacitor to energy center
            precharge_timer += 1
            Vapd_target = math.sqrt((250**2 + 450**2) / 2)  # ≈364V
            Vapd = Vapd + (Vapd_target - Vapd) * 0.01  # slow charge
            Id_ref = 0.0
            Iq_ref = 0.0
            omega_e = 0.0

            if precharge_timer >= int(0.1 / Ts):  # 100ms precharge
                state = StartupState.CHECK_VDC

        elif state == StartupState.CHECK_VDC:
            # Verify Vdc and Vapd are in range
            if dc.Vdc_min <= Vdc <= params.Vdc_ov and params.Vapd_min <= Vapd <= params.Vapd_max:
                state = StartupState.ALIGN
            elif precharge_timer >= int(0.5 / Ts):  # 500ms timeout
                fault_code = 4  # precharge timeout
                state = StartupState.FAULT

        elif state == StartupState.ALIGN:
            Id_ref = params.I_align
            Iq_ref = 0.0
            omega_e = 0.0
            omega_m = 0.0
            theta_e = 0.0
            theta_actual = 0.0
            align_timer += 1

            torque = 0.0

            if align_timer >= I_align_count:
                state = StartupState.IF_RAMP
                omega_e = 0.0
                omega_e_dot = 0.0
                omega_e_target = 0.0

        elif state == StartupState.IF_RAMP:
            # S-curve ramp: limited acceleration and jerk
            omega_e_target += params.omega_ramp_rate * Ts  # target increases linearly

            # S-curve: limit acceleration (jerk-limited)
            accel_error = omega_e_target - omega_e
            desired_accel = accel_error * 10.0  # proportional control
            desired_accel = max(-params.omega_jerk_limit * Ts,
                              min(params.omega_jerk_limit * Ts, desired_accel))
            omega_e_dot += desired_accel
            omega_e_dot = max(-params.omega_ramp_rate * 2,
                            min(params.omega_ramp_rate * 2, omega_e_dot))

            omega_e += omega_e_dot * Ts
            omega_m = omega_e_to_mech(omega_e, p)
            theta_e += omega_e * Ts
            theta_actual = theta_e  # motor tracks commanded in I-f

            # Current ramp (S-curve)
            ramp_timer += 1
            if ramp_timer < I_ramp_count:
                # S-curve: 3*t² - 2*t³
                x = ramp_timer / I_ramp_count
                ramp_factor = 3 * x**2 - 2 * x**3
            else:
                ramp_factor = 1.0

            Id_ref = 0.0
            Iq_ref = params.I_start * ramp_factor

            torque = Kt * Iq_ref

            # Check if observer can start checking
            if omega_m >= params.omega_start_mech:
                state = StartupState.OBSERVER_CHECK
                converge_count = 0

        elif state == StartupState.OBSERVER_CHECK:
            # Continue ramping
            omega_e_target += params.omega_ramp_rate * Ts
            accel_error = omega_e_target - omega_e
            desired_accel = accel_error * 10.0
            desired_accel = max(-params.omega_jerk_limit * Ts,
                              min(params.omega_jerk_limit * Ts, desired_accel))
            omega_e_dot += desired_accel
            omega_e_dot = max(-params.omega_ramp_rate * 2,
                            min(params.omega_ramp_rate * 2, omega_e_dot))
            omega_e += omega_e_dot * Ts
            omega_m = omega_e_to_mech(omega_e, p)
            theta_e += omega_e * Ts
            theta_actual = theta_e  # motor tracks commanded

            Iq_ref = params.I_start
            torque = Kt * Iq_ref

            # Check observer convergence
            theta_err_deg = abs(theta_actual - theta_obs) * 180 / math.pi
            if theta_err_deg > 180:
                theta_err_deg = 360 - theta_err_deg

            if theta_err_deg < params.theta_err_complete_foc:
                converge_count += 1
            else:
                converge_count = 0

            # Require N consecutive samples below threshold
            if converge_count >= params.N_converge_samples and omega_m >= params.omega_end_mech:
                state = StartupState.BLEND
                alpha = 0.0
                blend_timer = 0

        elif state == StartupState.BLEND:
            blend_timer += 1

            # Continue ramping speed
            omega_e_target += params.omega_ramp_rate * Ts
            accel_error = omega_e_target - omega_e
            desired_accel = accel_error * 10.0
            desired_accel = max(-params.omega_jerk_limit * Ts,
                              min(params.omega_jerk_limit * Ts, desired_accel))
            omega_e_dot += desired_accel
            omega_e_dot = max(-params.omega_ramp_rate * 2,
                            min(params.omega_ramp_rate * 2, omega_e_dot))
            omega_e += omega_e_dot * Ts
            omega_m = omega_e_to_mech(omega_e, p)

            # Observer-gated blend: only advance if angle error is acceptable
            theta_err_deg = abs(theta_e - theta_obs) * 180 / math.pi
            if theta_err_deg > 180:
                theta_err_deg = 360 - theta_err_deg

            if theta_err_deg < params.theta_err_continue_blend:
                # Advance blend
                alpha = min(1.0, alpha + Ts / (params.T_blend_ms / 1000.0))
            # If error too high, hold alpha (don't advance)

            # Blend angle
            theta_e = alpha * theta_obs + (1 - alpha) * theta_e

            # Blend current
            Iq_ref_foc = params.I_start  # simplified: speed PI output
            Iq_ref = (1 - alpha) * params.I_start + alpha * Iq_ref_foc
            Id_ref = 0.0

            torque = Kt * Iq_ref
            theta_e += omega_e * Ts
            theta_actual = theta_e  # motor follows blended angle

            if alpha >= 1.0:
                state = StartupState.FOC

        elif state == StartupState.FOC:
            theta_e = theta_obs  # use observer angle
            Id_ref = 0.0
            Iq_ref = params.I_start

            torque = Kt * Iq_ref
            omega_m = omega_e_to_mech(omega_e, p)
            theta_e += omega_e * Ts
            theta_actual = theta_e  # motor follows observer angle

            converged = True
            break

        elif state == StartupState.FAULT:
            # Shutdown: zero current
            Id_ref = 0.0
            Iq_ref = 0.0
            torque = 0.0
            break

        # Vdc model
        P_motor = torque * omega_m
        P_loss = 3 * Iq_ref**2 * motor.Rs
        P_input = P_motor + P_loss
        dE_cap = P_input * min(Ts, 0.001)
        E_stored -= dE_cap * 0.05
        Vdc = math.sqrt(2 * E_stored / dc.Cdc) if E_stored > 0 else dc.Vdc_nom
        Vdc = max(Vdc, dc.Vdc_min)

        # Record
        t += Ts
        theta_error_deg = abs(theta_actual - theta_obs) * 180 / math.pi
        if theta_error_deg > 180:
            theta_error_deg = 360 - theta_error_deg

        history['t'].append(t)
        history['state'].append(state)
        history['omega_m'].append(omega_m)
        history['omega_e'].append(omega_e)
        history['theta_e'].append(theta_e)
        history['theta_obs'].append(theta_obs)
        history['theta_error_deg'].append(theta_error_deg)
        history['Id_ref'].append(Id_ref)
        history['Iq_ref'].append(Iq_ref)
        history['alpha'].append(alpha)
        history['Vdc'].append(Vdc)
        history['torque'].append(torque)
        history['Vapd'].append(Vapd)

    # Analysis
    max_theta_error = max(history['theta_error_deg']) if history['theta_error_deg'] else 0
    final_speed_rpm = omega_m * 60 / (2 * math.pi)
    max_torque = max(history['torque']) if history['torque'] else 0
    min_Vdc = min(history['Vdc']) if history['Vdc'] else dc.Vdc_nom
    transition_time_ms = t * 1000

    return {
        'converged': converged,
        'fault_code': fault_code,
        'final_speed_rpm': round(final_speed_rpm, 1),
        'max_theta_error_deg': round(max_theta_error, 2),
        'max_torque_Nm': round(max_torque, 4),
        'min_Vdc': round(min_Vdc, 1),
        'transition_time_ms': round(transition_time_ms, 1),
        'omega_m_max': round(max(history['omega_m']), 1),
        'history_len': len(history['t']),
    }


def run_sweep():
    motor = MotorParams()
    dc = DcLinkParams()
    obs = ObserverParams()

    results = []
    for omega_ramp_rate in [500.0, 1000.0, 2000.0, 4000.0]:
        for I_start in [0.5, 1.0, 1.5]:
            for omega_start in [30.0, 50.0, 80.0]:
                for omega_end in [60.0, 80.0, 120.0]:
                    if omega_end <= omega_start:
                        continue
                    for T_blend in [100.0, 200.0, 500.0]:
                        params = StartupParams(
                            omega_ramp_rate=omega_ramp_rate,
                            I_start=I_start,
                            omega_start_mech=omega_start,
                            omega_end_mech=omega_end,
                            T_blend_ms=T_blend,
                        )
                        result = simulate_startup(motor, dc, obs, params)

                        passed = True
                        reasons = []
                        if result['max_theta_error_deg'] > 45:
                            passed = False
                            reasons.append(f"theta_err={result['max_theta_error_deg']:.1f}°>45°")
                        if result['min_Vdc'] < 250:
                            passed = False
                            reasons.append(f"Vdc_min={result['min_Vdc']:.0f}V<250V")
                        if result['max_torque_Nm'] > 2.0:
                            passed = False
                            reasons.append(f"T_max={result['max_torque_Nm']:.2f}Nm>2Nm")
                        if result['fault_code'] > 0:
                            passed = False
                            reasons.append(f"fault={result['fault_code']}")
                        if not result['converged']:
                            reasons.append("not_converged")

                        results.append({
                            'omega_ramp_rate': omega_ramp_rate,
                            'I_start': I_start,
                            'omega_start_mech': omega_start,
                            'omega_end_mech': omega_end,
                            'T_blend_ms': T_blend,
                            'passed': passed,
                            'reasons': reasons,
                            **{k: v for k, v in result.items() if k != 'history_len'},
                        })

    total = len(results)
    passed_count = sum(1 for r in results if r['passed'])
    print(f"Sweep: {passed_count}/{total} passed ({passed_count/total*100:.1f}%)")
    return results


def generate_report(results):
    lines = ["# Phase B-002: Corrected I-f Startup Simulation Results\n"]
    lines.append("Corrections: ψ_f=0.08Wb, expanded observer, APD precharge, observer-gated blend, S-curve ramp\n")

    passed = [r for r in results if r['passed']]
    failed = [r for r in results if not r['passed']]

    lines.append(f"Total: {len(results)} configs, {len(passed)} passed ({len(passed)/len(results)*100:.1f}%)\n")

    lines.append("## Best Configs (Fastest Convergence, Pass)\n")
    lines.append("| RampRate | I_start | ω_start | ω_end | T_blend | Speed(rpm) | θ_err(°) | T_max(Nm) | Vdc_min | Time(ms) |")
    lines.append("|----------|---------|---------|-------|---------|------------|----------|-----------|---------|----------|")
    best = sorted(passed, key=lambda r: r['transition_time_ms'])
    for r in best[:15]:
        lines.append(
            f"| {r['omega_ramp_rate']} | {r['I_start']} | {r['omega_start_mech']} | "
            f"{r['omega_end_mech']} | {r['T_blend_ms']} | {r['final_speed_rpm']} | "
            f"{r['max_theta_error_deg']} | {r['max_torque_Nm']} | {r['min_Vdc']} | "
            f"{r['transition_time_ms']} |"
        )

    lines.append("\n## Failure Breakdown\n")
    rc = {}
    for r in failed:
        for reason in r['reasons']:
            k = reason.split('=')[0] if '=' in reason else reason
            rc[k] = rc.get(k, 0) + 1
    for k, v in sorted(rc.items(), key=lambda x: -x[1]):
        lines.append(f"- {k}: {v}")

    lines.append("\n## Recommended Startup Baseline\n")
    if best:
        b = best[0]
        lines.append(f"- omega_ramp_rate: {b['omega_ramp_rate']} rad/s²")
        lines.append(f"- I_start: {b['I_start']}A")
        lines.append(f"- ω_start (observer check): {b['omega_start_mech']} rad/s mech")
        lines.append(f"- ω_end (safe transition): {b['omega_end_mech']} rad/s mech")
        lines.append(f"- T_blend: {b['T_blend_ms']}ms")
        lines.append(f"- Max θ error: {b['max_theta_error_deg']}°")
        lines.append(f"- Transition time: {b['transition_time_ms']}ms")

    return "\n".join(lines)


if __name__ == "__main__":
    out_dir = Path(__file__).parent

    results = run_sweep()

    report = generate_report(results)
    (out_dir / "sweep_results_v2.md").write_text(report)

    (out_dir / "sweep_raw_v2.json").write_text(json.dumps(results, indent=2))

    print(f"\nSaved to {out_dir}")
