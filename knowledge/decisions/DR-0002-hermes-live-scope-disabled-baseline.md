# DR-0002: Hermes Live Scope Disabled Baseline

Decision: hermes-gateway-lab live scope remains `allowed: []` and `not_enabled`. R4/R5 risk classes remain disabled.

Reason: Runtime enforcement of live gates is not yet verified. The worker gate function diverges from the canonical gate function. Enabling live execution before resolving this gap would be unsafe.

Status: Accepted
Date: 2026-05-27
Source: hermes-perm-audit-001, GPT architect + Codex convergence
