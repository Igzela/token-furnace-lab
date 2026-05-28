# Decision Record

## Decision: Accept derivation-005 as conditional research evidence

**Date:** 2026-05-28
**Status:** accepted

**Context:** The first derivation-005 sweep reported all practical configurations failing. GPT reviewed the model and found major issues, including DC-link energy balance using mechanical instead of electrical motor power. The corrected model was then reviewed by GPT and received `PASS_WITH_NOTES` (86/100).

**Decision:** Accept derivation-005 as conditional research evidence. Energy conservation and APD sanity checks pass. 100-200W is robust. 300W remains conditional on high nominal bus and high APD decoupling, and must not be presented as robust until APD branch and device-sizing checks are complete.

**Consequence:** The FOC/APD route remains open and viable. The next experiment should size the APD branch current, inductor, switching devices, capacitor tolerance, RMS/thermal behavior, and high-line device margins.
