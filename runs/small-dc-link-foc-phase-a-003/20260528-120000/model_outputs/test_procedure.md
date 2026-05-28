# Phase A-003: FOC Hardware Test Procedure

## Prerequisites

- TMS320F28035 board with 1360µF DC-link
- 3-phase BLDC/PMSM motor (p=4, Rs=2Ω, Ls=5mH, ψ_f=0.08Wb)
- DC power supply (0-400V, 5A)
- Current probes (2 channels, ±5A)
- Oscilloscope (200MHz+)
- External voltage meter for Vdc verification

## Safety Interlocks (BEFORE Any PWM-to-Motor Test)

- [ ] Hardware emergency stop functional
- [ ] PWM trip-zone verified
- [ ] Overcurrent comparator verified
- [ ] DC bus precharge/discharge check
- [ ] UVLO/OV thresholds tested with simulated input
- [ ] ADC saturation detection enabled
- [ ] PWM disabled on watchdog reset
- [ ] Fault latch requires manual clear
- [ ] Maximum duty clamp set
- [ ] Maximum Iq clamp set (0.5A initially)
- [ ] Startup timeout configured

## Conservative Initial Limits

| Parameter | Initial | Final | Rationale |
|-----------|---------|-------|-----------|
| OC threshold | 2A | 5A | Lower for first tests |
| Iq max | 0.5A | 3.0A | Conservative start |
| PWM duty max | 0.8 | 0.95 | Leave margin |
| Vdc test | 300V | 300V | Nominal |

## A-003.0: Fixed-Point Scaling Dry Test (MANDATORY)

**No motor power. No PWM to motor.**

### Test Steps

1. **Q15 current conversion**
   - ADC raw → amps → Q15 → amps
   - Verify round-trip error < 1%

2. **Vdc conversion**
   - ADC raw → volts → Q15/q12 monitor
   - Verify scaling factor correct

3. **angle_t wrap**
   - Test: 0°, 90°, 180°, 270°, 360°
   - Verify wrap behavior (0° = 360° = 0)

4. **sin/cos lookup**
   - Verify sin(0°)=0, sin(90°)=1, sin(180°)=0
   - Verify cos(0°)=1, cos(90°)=0, cos(180°)=-1

5. **Park/Inverse Park round-trip**
   - Input: (I_alpha, I_beta, theta)
   - Forward: → (Id, Iq)
   - Inverse: → (I_alpha', I_beta')
   - Verify: I_alpha' ≈ I_alpha, I_beta' ≈ I_beta

6. **SVPWM known vectors**
   - theta = 0°: alpha→d, beta→q
   - theta = 90°: rotation signs verified

7. **IqLimiter known cases**
   - Vdc = 300V, omega = 100 rad/s → expected Iq_max
   - Vdc = 216V, omega = 4000 rpm → Iq_max reduced

8. **PI gain scaling**
   - KiTs at 10kHz: verify integration step
   - Saturation arithmetic behavior

### Pass Criteria
- All conversions round-trip < 1% error
- angle_t wrap correct
- sin/cos within 0.5% of theoretical
- Park round-trip < 1% error
- IqLimiter matches derivation-003 table

## A-003.1: Hardware Measurement Sanity

### Setup
- Power supply at 300V DC
- Motor disconnected (no load)
- All safety checks verified

### Test Steps
1. **ADC offset calibration**
   - Record ADC values with no current (Id=Iq=0)
   - Verify offset < 10 LSB
   - Expected: ~2048 (mid-scale for 12-bit ADC)

2. **Vdc measurement**
   - Read Vdc from ADC
   - Compare with external meter
   - Tolerance: ±2% (294-306V at 300V nominal)

3. **PWM output verification**
   - Enable PWM at 50% duty
   - Scope phase A, B, C outputs
   - Verify: complementary pairs, deadtime present, no shoot-through

4. **Current polarity**
   - Apply small Id_ref = 0.1A
   - Verify current probe reads positive on phase A
   - If negative: swap current sensor wiring or invert ADC channel

### Pass Criteria
- ADC offset < 10 LSB
- Vdc error < 2%
- PWM complementary pairs verified
- Current polarity correct

### Fail Actions
- ADC offset > 10 LSB → recalibrate or check hardware
- Vdc error > 2% → check voltage divider ratio
- PWM not complementary → check deadtime module
- Current polarity wrong → swap sensor wires or invert in software

## A-003.2: Open-Loop Voltage Vector Test

### Setup
- Motor connected, free to rotate
- Vdc = 300V
- No current control (open-loop voltage)

### Test Steps
1. **Apply small voltage vector**
   - Set Vd = 5V (small fraction of Vdc)
   - Vq = 0
   - Duration: 100ms
   - Verify motor shaft rotates slightly

2. **Verify direction**
   - Apply +Vd → motor should rotate in one direction
   - Apply -Vd → motor should rotate opposite
   - If same direction: Park transform sign error

3. **Scope current**
   - Current should be small (limited by back-EMF at standstill)
   - No large spikes or oscillations

### Pass Criteria
- Motor responds to voltage command
- Direction correct for +Vd and -Vd
- Current bounded (< 1A at 5V applied)

## A-003.3: Current-Loop Validation

### Setup
- Motor connected, free to rotate
- Vdc = 300V
- Current PI active (Kp=120.54, Ki=70440)
- Speed PI disabled (open-loop speed)

### Test Steps
1. **Id regulation**
   - Set Id_ref = 0.2A, Iq_ref = 0
   - Verify |Id_meas - Id_ref| < 10%
   - Verify Iq ≈ 0 (decoupling working)

2. **Iq step response**
   - Set Iq_ref = 0.2A
   - Step to 0.5A
   - Step to 1.0A
   - Verify: overshoot < 20%, settling time < 10ms

3. **Cross-coupling test**
   - Set Id_ref = 0.5A, Iq_ref = 0.5A
   - Verify both channels track independently
   - Cross-coupling < 10%

4. **Stability check**
   - Run for 5 seconds at Iq = 1.0A
   - No current oscillations or divergence
   - Motor heats up normally (no excessive loss)

### Pass Criteria
- Id tracking error < 10%
- Iq overshoot < 20%
- Settling time < 10ms
- Cross-coupling < 10%
- No instability over 5s run

### Fail Actions
- Large tracking error → retune PI gains
- Overshoot > 20% → reduce Kp or increase Ki
- Cross-coupling > 10% → improve feed-forward decoupling
- Instability → reduce gains, check ADC sampling

## A-003.4: SVPWM + Vdc Feedforward

### Setup
- Current PI active
- Iq_ref = 0.5A
- Vdc = 300V

### Test Steps
1. **Modulation index**
   - Calculate m = V_req / (Vdc/√3)
   - At low speed: m should be small (< 0.3)
   - At medium speed: m increases

2. **Saturation behavior**
   - Increase Iq_ref until SVPWM saturates
   - Verify saturation flag triggers
   - Verify IqLimiter reduces Iq_ref

3. **Vdc feedforward**
   - Change Vdc from 300V to 250V
   - Verify modulation index adjusts
   - Current regulation should remain stable

### Pass Criteria
- Modulation index < 1.0 in normal operation
- Saturation flag triggers at expected point
- IqLimiter limits correctly
- Vdc change doesn't cause instability

## A-003.5: Observer Passive Validation

### Setup
- Motor running under I-f or open-loop at medium speed
- SMO running in background (not used for control)
- theta_source = ramp (not observer)

### Test Steps
1. **Run motor at 200 rad/s electrical**
   - I-f ramp to medium speed
   - Log theta_ramp and theta_obs

2. **Compare theta**
   - theta_obs should track theta_ramp with small offset
   - Offset should be consistent (not oscillating)
   - θ_err < 30° at medium speed

3. **Noise check**
   - theta_obs should not have large jumps
   - No 180° phase wraps during operation

### Pass Criteria
- θ_err < 30° at 200 rad/s
- No 180° jumps
- Consistent offset (not oscillating)

## A-003.6: Sensorless Handover Dry Run

### Setup
- Motor running under I-f at medium speed
- theta_source_mux in logging mode (not switching)
- Observer active

### Test Steps
1. **Ramp to handover speed**
   - I-f ramp to omega_end (60 rad/s mech)
   - Log all signals: theta_ramp, theta_obs, theta_err, alpha

2. **Verify handover conditions**
   - theta_err < 20° for 200 samples → handover ready
   - Log but don't execute transition

3. **Post-analysis**
   - Plot theta_ramp vs theta_obs
   - Verify three-threshold detection works
   - Check anti-chatter behavior

### Pass Criteria
- theta_err decreases monotonically during ramp
- Handover conditions met at expected speed
- No anomalous behavior in log

## Risk Assessment for Phase D

| Risk | Impact | Mitigation |
|------|--------|------------|
| FOC current loop unstable | Cannot run motor | A-003.3 validates |
| SMO doesn't converge | No sensorless operation | A-003.5 validates |
| 22µF ripple too large | Vdc drops below UVLO | A-003 validates on 1360µF first |
| APD precharge fails | Cannot start | Tested separately in Phase D |
| Fixed-point overflow | Incorrect control output | Q15/Q12 scaling verified |
