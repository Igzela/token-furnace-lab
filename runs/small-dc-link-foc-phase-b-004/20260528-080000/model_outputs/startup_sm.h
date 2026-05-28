#ifndef STARTUP_SM_H
#define STARTUP_SM_H

#include <stdint.h>

/* === State Machine States === */
typedef enum {
    SM_IDLE          = 0,
    SM_PRECHARGE     = 1,
    SM_ALIGN         = 2,
    SM_IF_RAMP       = 3,
    SM_OBSERVER_CHECK= 4,
    SM_BLEND         = 5,
    SM_FOC           = 6,
    SM_FAULT         = 7
} StartupState;

/* === Fault Codes (GPT corrected: added timeout/observer faults) === */
typedef enum {
    FAULT_OK                 = 0,
    FAULT_UVLO               = 1,
    FAULT_OV                 = 2,
    FAULT_OC                 = 3,
    FAULT_PRECHARGE_TMO      = 4,
    FAULT_BLEND_ABORT        = 5,
    FAULT_OBSERVER_LOST      = 6,
    FAULT_APD                = 7,
    FAULT_USER               = 8,
    FAULT_OBSERVER_LOCK_TMO  = 9,
    FAULT_SVPWM_SAT_TMO     = 10,
    FAULT_STARTUP_TMO        = 11,
    FAULT_THETA_JUMP         = 12,
    FAULT_STALL              = 13,
    FAULT_LATCHED            = 14
} FaultCode;

/* === Angle Type (GPT: use uint16_t, not q12) === */
/* 0..65535 maps to 0..2π. Wraps naturally. */
typedef uint16_t angle_t;

#define ANGLE_45_DEG  8192    /* 45° × 65536/360 */
#define ANGLE_35_DEG  6372    /* 35° */
#define ANGLE_30_DEG  5461    /* 30° */
#define ANGLE_20_DEG  3641    /* 20° */
#define ANGLE_5_DEG   910     /* 5°  */
#define ANGLE_180_DEG 32768   /* 180° */

/* Signed wrapped angle difference: result in [-180°, +180°] as angle_t */
static inline int16_t angle_diff(angle_t a, angle_t b) {
    return (int16_t)(a - b);
}

/* === Three Thresholds (GPT corrected: angle_t, not degrees) === */
#define THETA_DETECT   ANGLE_45_DEG   /* observer detected */
#define THETA_BLEND    ANGLE_30_DEG   /* blend allowed */
#define THETA_ROLLBACK ANGLE_35_DEG   /* anti-chatter freeze */
#define THETA_FOC      ANGLE_20_DEG   /* FOC handover */

/* === Dwell Counters (all at 10kHz ISR rate) === */
#define PRECHARGE_DWELL_TICKS    1000    /* 100ms at 10kHz */
#define ALIGN_DWELL_TICKS        2000    /* 200ms at 10kHz */
#define HANDOVER_N_SAMPLES       200     /* 20ms at 10kHz */
#define OBSERVER_INVALID_TICKS   50      /* 5ms at 10kHz */
#define STARTUP_TIMEOUT_TICKS    50000   /* 5s max startup */
#define SVPWM_SAT_TIMEOUT_TICKS  5000    /* 500ms max SVPWM saturation */

/* === Blend Parameters (GPT: 0.1% advance, 0.5-1.0% rollback) === */
#define ALPHA_ADVANCE_STEP   1     /* α × 1000 per sample = 0.1% (100ms blend at 10kHz) */
#define ALPHA_ROLLBACK_STEP  5     /* α × 1000 per sample = 0.5% (aggressive rollback) */

/* === Fault Thresholds === */
#define VDC_UVLO_MV             200000
#define VDC_OV_MV               450000
#define VDC_MIN_MV              250000
#define VDC_MAX_MV              450000
#define VAPD_MIN_MV             200000
#define VAPD_MAX_MV             500000
#define OC_THRESHOLD_MA         5000

/* === Trace Flags (packed bits) === */
#define TRACE_FLAG_OBSERVER_VALID   (1 << 0)
#define TRACE_FLAG_SPEED_VALID      (1 << 1)
#define TRACE_FLAG_SVPWM_SAT        (1 << 2)
#define TRACE_FLAG_IQ_LIMITED       (1 << 3)
#define TRACE_FLAG_APD_READY        (1 << 4)
#define TRACE_FLAG_UVLO             (1 << 5)
#define TRACE_FLAG_OV               (1 << 6)
#define TRACE_FLAG_OC               (1 << 7)

/* === Compact Trace Entry (16 bytes × 128 = 2KB, GPT corrected) === */
typedef struct {
    uint16_t tick;          /* 16-bit timestamp (wraps at 6.5s at 10kHz) */
    uint8_t  state;
    uint8_t  fault_code;
    int16_t  theta_err;     /* signed wrapped millidegrees */
    uint16_t alpha_x1000;   /* α × 1000 */
    int16_t  omega_ref_x10; /* rad/s mech × 10 */
    int16_t  omega_est_x10;
    int16_t  iq_ref_ma;
    int16_t  iq_meas_ma;
    uint16_t vdc_mv;
    uint16_t vapd_mv;
    uint8_t  flags;         /* packed: see TRACE_FLAG_* */
    uint8_t  _pad;
} CompactTraceEntry;        /* 16 bytes */

#define TRACE_DEPTH 128     /* 2KB total */

/* === Startup Profiles with Escalation === */
typedef struct {
    uint16_t I_start_ma;
    uint16_t omega_start_x10;   /* rad/s mech × 10 */
    uint16_t omega_end_x10;
    uint16_t T_blend_ms;
    uint8_t  profile_id;        /* 0=nominal, 1=fallback, 2=strong */
} StartupProfile;

#define PROFILE_NOMINAL  { 500,  300, 600, 100, 0 }
#define PROFILE_FALLBACK { 800,  300, 600, 150, 1 }
#define PROFILE_STRONG   { 1000, 300, 600, 200, 2 }

#define STARTUP_RETRY_MAX  3    /* after 3 fails → FAULT_LATCHED */
#define STARTUP_COOLDOWN_TICKS 10000  /* 1s cooldown between retries */

/* === State Machine Context === */
typedef struct {
    StartupState state;
    FaultCode    fault;
    StartupProfile profile;

    /* Dwell counters (all 10kHz ISR rate) */
    uint16_t precharge_dwell;
    uint16_t align_dwell;
    uint16_t handover_counter;
    uint16_t observer_invalid_counter;
    uint16_t startup_timer;
    uint16_t svpwm_sat_timer;

    /* Retry / escalation */
    uint8_t  retry_count;
    uint16_t cooldown_timer;
    uint8_t  fault_latched;

    /* Flags (sticky once set) */
    uint8_t observer_detected;
    uint8_t blend_allowed;
    uint8_t current_stable;
    uint8_t svpwm_saturated;

    /* Blend state */
    uint16_t alpha_x1000;       /* 0-1000 */
    angle_t  theta_ramp;
    angle_t  theta_obs;
    angle_t  theta_blend;

    /* I-f ramp state (electrical rad/s as q12) */
    int32_t  omega_e_x4096;
    int32_t  omega_e_dot_x4096;
    int32_t  theta_e_x4096;
    int16_t  ramp_timer;

    /* Current references */
    int16_t  Id_ref_ma;
    int16_t  Iq_ref_ma;

    /* Trace */
    CompactTraceEntry trace[TRACE_DEPTH];
    uint16_t   trace_idx;
    uint8_t    trace_full;
} StartupContext;

/* === API === */
void startup_init(StartupContext *ctx, const StartupProfile *profile);
void startup_reset(StartupContext *ctx);
StartupState startup_step(StartupContext *ctx,
                          uint16_t vdc_mv, uint16_t vapd_mv,
                          int16_t iq_meas_ma,
                          angle_t theta_obs,
                          int16_t omega_est_x10,
                          uint8_t svpwm_saturated);
void startup_log_trace(StartupContext *ctx,
                       int16_t iq_meas_ma,
                       angle_t theta_obs,
                       int16_t omega_est_x10,
                       uint16_t vdc_mv, uint16_t vapd_mv,
                       uint8_t svpwm_saturated);

#endif /* STARTUP_SM_H */
