# Phase A-002: GPT Review History

## v1 → v2 (74/100 → 86/100)

### GPT v1 Feedback (74/100 PASS_WITH_NOTES)
1. Module count: 9 listed, should clarify 7 core + 2 peripheral
2. Missing interfaces: ADC calibration/faults, SVPWM saturation, SMO valid/lock, Speed Ref flags
3. **Critical**: theta_source_mux missing — Park can't unconditionally take theta_est
4. **Fixed-point base units undefined**: q15_t needs I_base, V_base, omega_base
5. **PI gains are continuous-time**: Kp=120.54, Ki=70440 can't fit in q12_t — need gain_t
6. ISR: speed loop can be 10kHz sub-task
7. Missing IqLimiter interface from derivation-003
8. RAM budget needs explicit exclusions

### v2 Changes Applied
1. Added theta_source_mux (OPEN_LOOP/SENSORLESS/BLEND)
2. Added IqLimiter interface
3. Defined base units (I_base=5A, V_base=400V, omega_base=500 rad/s)
4. Added gain_t with discrete Q16 format
5. Added ADC calibration/fault flags
6. Added SMO valid/speed_valid status
7. ISR: speed loop as 10kHz sub-task
8. Added SVPWM modulation_index/saturated output
9. Expanded Speed Ref fields
10. RAM budget clarified

## v2 → v3 (86/100 → address final notes)

### GPT v2 Feedback (86/100 PASS_WITH_NOTES)
1. **omega_base=500 only covers mechanical, not electrical omega** (omega_e = 4×419 ≈ 1676 rad/s)
2. **SMO input should use applied voltage, not command voltage** (reconstructed from PWM duty + Vdc)
3. **vdc_monitor range**: q15 saturates at 400V, need q12 path for >400V overvoltage detection
4. PI gains: must document KiTs is discrete (Ki × Ts), not continuous Ki
5. ISR: speed loop double-buffering for iq_ref
6. SVPWM: modulation_index and saturated outputs important for downstream

### v3 Changes Applied
1. Split omega: omega_m_base=500 (q15, mechanical), omega_e_base=2000 (q12, electrical)
2. SMO input: v_alpha_applied reconstructed from PWM duty + Vdc
3. ADC output: added vdc_mon (q12, Vdc_mon_base=500V) for protection
4. SMO output: omega_est_e (q12, electrical) → converted to omega_m_est for Speed PI
5. IqLimiter input: omega_est_e (q12, electrical)
6. Speed PI input: omega_m_est (q15, mechanical)
7. ISR flow: explicit omega conversion step, iq_ref double-buffering note
