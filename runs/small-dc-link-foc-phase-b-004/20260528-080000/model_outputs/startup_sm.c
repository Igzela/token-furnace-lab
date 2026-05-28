#include "startup_sm.h"
#include <string.h>

#define ABS(x) ((x) < 0 ? -(x) : (x))
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : ((v) > (hi) ? (hi) : (v)))

static uint8_t build_flags(const StartupContext *ctx, uint16_t vdc_mv, uint16_t vapd_mv) {
    uint8_t f = 0;
    if (ctx->observer_detected)   f |= TRACE_FLAG_OBSERVER_VALID;
    if (!ctx->svpwm_saturated)    f |= TRACE_FLAG_SPEED_VALID;
    if (ctx->svpwm_saturated)     f |= TRACE_FLAG_SVPWM_SAT;
    if (ABS(ctx->Iq_ref_ma) > ctx->profile.I_start_ma) f |= TRACE_FLAG_IQ_LIMITED;
    if (vapd_mv >= VAPD_MIN_MV && vapd_mv <= VAPD_MAX_MV) f |= TRACE_FLAG_APD_READY;
    if (vdc_mv < VDC_UVLO_MV)    f |= TRACE_FLAG_UVLO;
    if (vdc_mv > VDC_OV_MV)      f |= TRACE_FLAG_OV;
    return f;
}

static void log_entry(StartupContext *ctx,
                      int16_t iq_meas, angle_t obs,
                      int16_t omega_est, uint16_t vdc, uint16_t vapd,
                      uint8_t sat) {
    CompactTraceEntry *e = &ctx->trace[ctx->trace_idx];
    e->tick           = (uint16_t)(ctx->startup_timer & 0xFFFF);
    e->state          = ctx->state;
    e->fault_code     = ctx->fault;
    e->theta_err      = angle_diff(ctx->theta_ramp, ctx->theta_obs);
    e->alpha_x1000    = ctx->alpha_x1000;
    e->omega_ref_x10  = (int16_t)(ctx->omega_e_x4096 * 10 / 4096);
    e->omega_est_x10  = omega_est;
    e->iq_ref_ma      = ctx->Iq_ref_ma;
    e->iq_meas_ma     = iq_meas;
    e->vdc_mv         = vdc;
    e->vapd_mv        = vapd;
    e->flags          = build_flags(ctx, vdc, vapd);
    e->_pad           = 0;

    ctx->trace_idx = (ctx->trace_idx + 1) % TRACE_DEPTH;
    if (ctx->trace_idx == 0) ctx->trace_full = 1;
}

void startup_init(StartupContext *ctx, const StartupProfile *profile) {
    memset(ctx, 0, sizeof(*ctx));
    ctx->state = SM_IDLE;
    ctx->fault = FAULT_OK;
    ctx->profile = *profile;
}

void startup_reset(StartupContext *ctx) {
    StartupProfile p = ctx->profile;
    uint8_t retries = ctx->retry_count;
    startup_init(ctx, &p);
    ctx->retry_count = retries;
}

static void escalate_profile(StartupContext *ctx) {
    ctx->retry_count++;
    if (ctx->retry_count >= STARTUP_RETRY_MAX) {
        ctx->fault = FAULT_LATCHED;
        ctx->state = SM_FAULT;
        return;
    }
    /* Escalate: nominal→fallback→strong */
    if (ctx->profile.profile_id == 0) {
        ctx->profile = (StartupProfile)PROFILE_FALLBACK;
    } else if (ctx->profile.profile_id == 1) {
        ctx->profile = (StartupProfile)PROFILE_STRONG;
    }
    ctx->cooldown_timer = STARTUP_COOLDOWN_TICKS;
}

StartupState startup_step(StartupContext *ctx,
                          uint16_t vdc_mv, uint16_t vapd_mv,
                          int16_t iq_meas_ma,
                          angle_t theta_obs,
                          int16_t omega_est_x10,
                          uint8_t svpwm_saturated) {
    ctx->svpwm_saturated = svpwm_saturated;
    ctx->startup_timer++;

    /* === FAULT CHECKS (all states except FAULT) === */
    if (ctx->state != SM_FAULT) {
        if (vdc_mv < VDC_UVLO_MV) {
            ctx->fault = FAULT_UVLO; ctx->state = SM_FAULT; goto done;
        }
        if (vdc_mv > VDC_OV_MV) {
            ctx->fault = FAULT_OV; ctx->state = SM_FAULT; goto done;
        }
        if (ABS(iq_meas_ma) > OC_THRESHOLD_MA || ABS(ctx->Id_ref_ma) > OC_THRESHOLD_MA) {
            ctx->fault = FAULT_OC; ctx->state = SM_FAULT; goto done;
        }
        /* Global startup timeout */
        if (ctx->startup_timer >= STARTUP_TIMEOUT_TICKS && ctx->state < SM_FOC) {
            ctx->fault = FAULT_STARTUP_TMO; ctx->state = SM_FAULT; goto done;
        }
        /* SVPWM saturation timeout */
        if (ctx->svpwm_saturated) {
            ctx->svpwm_sat_timer++;
            if (ctx->svpwm_sat_timer >= SVPWM_SAT_TIMEOUT_TICKS) {
                ctx->fault = FAULT_SVPWM_SAT_TMO; ctx->state = SM_FAULT; goto done;
            }
        } else {
            ctx->svpwm_sat_timer = 0;
        }
    }

    switch (ctx->state) {
    case SM_IDLE:
        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = 0;
        break;

    case SM_PRECHARGE:
        ctx->precharge_dwell++;
        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = 0;
        /* Gated transition: dwell + conditions */
        if (ctx->precharge_dwell >= PRECHARGE_DWELL_TICKS &&
            vdc_mv >= VDC_MIN_MV && vdc_mv <= VDC_MAX_MV &&
            vapd_mv >= VAPD_MIN_MV && vapd_mv <= VAPD_MAX_MV) {
            ctx->state = SM_ALIGN;
        } else if (ctx->precharge_dwell >= 5000) {
            ctx->fault = FAULT_PRECHARGE_TMO; ctx->state = SM_FAULT;
        }
        break;

    case SM_ALIGN:
        ctx->align_dwell++;
        ctx->Id_ref_ma = ctx->profile.I_start_ma;
        ctx->Iq_ref_ma = 0;
        ctx->omega_e_x4096 = 0;
        ctx->theta_e_x4096 = 0;
        /* Gated: dwell + current stable + PWM active */
        if (ctx->align_dwell >= ALIGN_DWELL_TICKS &&
            !ctx->svpwm_saturated) {
            ctx->state = SM_IF_RAMP;
            ctx->ramp_timer = 0;
            ctx->omega_e_dot_x4096 = 0;
        }
        break;

    case SM_IF_RAMP: {
        ctx->ramp_timer++;
        /* S-curve ramp */
        int32_t target_e = (int32_t)ctx->profile.omega_end_x10 * 4096 / 10;
        int32_t accel_error = (target_e - ctx->omega_e_x4096) * 10;
        accel_error = CLAMP(accel_error, -20480, 20480);
        ctx->omega_e_dot_x4096 += accel_error;
        ctx->omega_e_dot_x4096 = CLAMP(ctx->omega_e_dot_x4096, -409600, 409600);
        ctx->omega_e_x4096 += ctx->omega_e_dot_x4096 / 1000;
        ctx->theta_e_x4096 += ctx->omega_e_x4096 / 1000;
        ctx->theta_ramp = (angle_t)(ctx->theta_e_x4096 & 0xFFFF);
        ctx->theta_obs = theta_obs;

        /* Current S-curve ramp */
        int32_t ramp_count = 1000;
        if (ctx->ramp_timer < ramp_count) {
            float x = (float)ctx->ramp_timer / ramp_count;
            float ramp = 3.0f * x * x - 2.0f * x * x * x;
            ctx->Iq_ref_ma = (int16_t)(ctx->profile.I_start_ma * ramp);
        } else {
            ctx->Iq_ref_ma = ctx->profile.I_start_ma;
        }
        ctx->Id_ref_ma = 0;

        /* Observer detection */
        int16_t err = angle_diff(ctx->theta_ramp, ctx->theta_obs);
        if (ABS(err) < ANGLE_45_DEG) ctx->observer_detected = 1;

        /* Gated: observer detected + speed sufficient + observer input valid */
        int32_t omega_m_x10 = omega_est_x10;
        if (ctx->observer_detected &&
            omega_m_x10 >= ctx->profile.omega_start_x10 &&
            !ctx->svpwm_saturated) {
            ctx->state = SM_OBSERVER_CHECK;
            ctx->handover_counter = 0;
            ctx->observer_invalid_counter = 0;
        }
        break;
    }

    case SM_OBSERVER_CHECK: {
        /* Continue ramping */
        ctx->ramp_timer++;
        int32_t target_e = (int32_t)ctx->profile.omega_end_x10 * 4096 / 10;
        int32_t accel_error = (target_e - ctx->omega_e_x4096) * 10;
        accel_error = CLAMP(accel_error, -20480, 20480);
        ctx->omega_e_dot_x4096 += accel_error;
        ctx->omega_e_dot_x4096 = CLAMP(ctx->omega_e_dot_x4096, -409600, 409600);
        ctx->omega_e_x4096 += ctx->omega_e_dot_x4096 / 1000;
        ctx->theta_e_x4096 += ctx->omega_e_x4096 / 1000;
        ctx->theta_ramp = (angle_t)(ctx->theta_e_x4096 & 0xFFFF);
        ctx->theta_obs = theta_obs;

        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = ctx->profile.I_start_ma;

        /* Three-threshold check */
        int16_t err = angle_diff(ctx->theta_ramp, ctx->theta_obs);
        if (ABS(err) < ANGLE_45_DEG) ctx->observer_detected = 1;
        if (ctx->observer_detected && ABS(err) < ANGLE_30_DEG) {
            ctx->blend_allowed = 1;
        }

        if (ABS(err) < ANGLE_20_DEG) {
            ctx->handover_counter++;
        } else {
            ctx->handover_counter = 0;
        }

        /* Gated: blend allowed + speed sufficient */
        int32_t omega_m_x10 = omega_est_x10;
        if (ctx->blend_allowed &&
            omega_m_x10 >= ctx->profile.omega_end_x10) {
            ctx->state = SM_BLEND;
            ctx->alpha_x1000 = 0;
            ctx->observer_invalid_counter = 0;
            ctx->handover_counter = 0;
        }
        break;
    }

    case SM_BLEND: {
        int16_t err = angle_diff(ctx->theta_ramp, ctx->theta_obs);
        int16_t abs_err = ABS(err);

        /* GPT-corrected blend: 0.1% advance, 0.5% rollback, hysteresis */
        if (abs_err < ANGLE_30_DEG) {
            ctx->alpha_x1000 = CLAMP(ctx->alpha_x1000 + ALPHA_ADVANCE_STEP, 0, 1000);
        } else if (abs_err > ANGLE_35_DEG && abs_err <= ANGLE_45_DEG) {
            ctx->alpha_x1000 = CLAMP(ctx->alpha_x1000 - ALPHA_ROLLBACK_STEP, 0, 1000);
        }
        /* else: freeze (between 30° and 35°, or >45° handled below) */

        /* Observer invalid: different behavior by severity */
        if (abs_err > ANGLE_45_DEG) {
            ctx->observer_invalid_counter++;
            if (ctx->observer_invalid_counter >= OBSERVER_INVALID_TICKS) {
                /* Rollback to OBSERVER_CHECK, not FAULT */
                ctx->state = SM_OBSERVER_CHECK;
                ctx->alpha_x1000 = 0;
                ctx->blend_allowed = 0;
                ctx->handover_counter = 0;
                ctx->observer_invalid_counter = 0;
                break;
            }
        } else {
            ctx->observer_invalid_counter = 0;
        }

        /* Blend angle */
        uint32_t blended = ((uint32_t)ctx->alpha_x1000 * (uint32_t)ctx->theta_obs +
                            (1000 - ctx->alpha_x1000) * (uint32_t)ctx->theta_ramp) / 1000;
        ctx->theta_blend = (angle_t)(blended & 0xFFFF);
        ctx->theta_ramp = ctx->theta_blend;

        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = ctx->profile.I_start_ma;

        /* FOC handover */
        if (abs_err < ANGLE_20_DEG) {
            ctx->handover_counter++;
        } else {
            ctx->handover_counter = 0;
        }

        if (ctx->handover_counter >= HANDOVER_N_SAMPLES) {
            ctx->state = SM_FOC;
        }
        break;
    }

    case SM_FOC:
        ctx->theta_blend = theta_obs;
        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = ctx->profile.I_start_ma;

        /* Observer lost during FOC */
        {
            int16_t err = angle_diff(ctx->theta_blend, theta_obs);
            if (ABS(err) > ANGLE_45_DEG) {
                ctx->fault = FAULT_OBSERVER_LOST;
                ctx->state = SM_FAULT;
            }
        }
        break;

    case SM_FAULT:
        ctx->Id_ref_ma = 0;
        ctx->Iq_ref_ma = 0;
        /* Retry with escalation if not latched */
        if (!ctx->fault_latched && ctx->cooldown_timer > 0) {
            ctx->cooldown_timer--;
        } else if (!ctx->fault_latched && ctx->cooldown_timer == 0) {
            escalate_profile(ctx);
            if (ctx->fault != FAULT_LATCHED) {
                startup_reset(ctx);
                ctx->state = SM_PRECHARGE;
                ctx->retry_count++; /* preserve retry count through reset */
            }
        }
        break;
    }

done:
    return ctx->state;
}

void startup_log_trace(StartupContext *ctx,
                       int16_t iq_meas, angle_t theta_obs,
                       int16_t omega_est, uint16_t vdc, uint16_t vapd,
                       uint8_t svpwm_sat) {
    log_entry(ctx, iq_meas, theta_obs, omega_est, vdc, vapd, svpwm_sat);
}
