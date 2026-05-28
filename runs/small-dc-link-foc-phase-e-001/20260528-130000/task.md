# Phase E-001: Runtime Fault Recovery and Safe Degradation

## Goal

Design fault-state transition matrix and recovery strategies for when the system leaves the happy path. Directly affects hardware safety.

## Fault Cases to Address

1. Observer loses lock during FOC
2. Vdc drops below voltage-margin threshold
3. APD saturates or loses readiness
4. SVPWM saturation persists
5. IqLimiter clamps for too long
6. Overcurrent trip during startup
7. Pump stalls or fails to accelerate
8. Sensor offset drift after startup

## Required Outputs

1. Fault-state transition matrix (state → state with conditions)
2. Recovery strategy for each fault type
3. Degradation modes (what gets reduced before full fault)
4. Restart/retry logic
5. GPT review
