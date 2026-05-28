# Phase A-003: FOC Hardware Baseline Validation on 1360µF DC-Link

## Goal

Validate core FOC and measurement chain on stable 1360µF DC-link before adding 22µF/APD complexity.

## Input Conditions

- DC-link: 1360µF (known-good hardware)
- Vdc_nominal: 300V
- APD: disabled
- Startup: conservative / open-loop or low-speed test only

## Non-Goals

- No 22µF test
- No APD
- No aggressive startup
- No final sensorless claims

## Milestones

### A-003.1: Hardware Measurement Sanity
- ADC current offsets calibrated and stable
- Vdc measurement matches external meter
- PWM duty and phase sequence verified
- Current polarity correct

### A-003.2: Open-Loop Voltage Vector Test
- Small voltage vector applied
- No closed-loop current PI yet
- Verify motor responds to voltage command

### A-003.3: Current-Loop Validation
- Id/Iq closed-loop on stable DC-link
- Low current limit (Iq_ref: 0.2A → 0.5A → 1.0A)
- Current PI tracks references without instability

### A-003.4: SVPWM + Vdc Feedforward
- Modulation index check
- Saturation behavior verified
- IqLimiter produces expected limits

### A-003.5: Observer Passive Validation
- SMO running in background (not used for control)
- SMO theta follows expected trend at medium speed

### A-003.6: Sensorless Handover Dry Run
- theta_source_mux logging only
- No automatic full transition
- Log all signals for post-analysis

## Acceptance Criteria

### Minimum Pass
1. ADC current offsets calibrated
2. Vdc measurement within tolerance
3. PWM phase sequence correct
4. Clarke/Park outputs correct sign and scaling
5. Current PI stable
6. SVPWM saturation flag works
7. IqLimiter limits correct
8. Trace buffer within RAM budget
9. Fault exits trigger correctly

### Strong Pass
1. Motor runs under controlled FOC
2. Id≈0 regulation works
3. Iq step response bounded and stable
4. Speed estimate plausible
5. SMO theta follows expected trend
6. No unexplained current spikes

## Required Outputs

1. Test procedure for each milestone
2. Pass/fail criteria with measurement targets
3. GPT review of test plan
4. Risk assessment for Phase D integration
