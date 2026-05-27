# Permission Boundary Model

Observation: hermes-gateway-lab defines a 5-scope permission model (read, plan, approval.local, dry_run, live) with explicit risk classes R0-R5.

Rule candidate: Permission architectures should define scopes, risk classes, and gate checklists as separate concerns. Scope defines what, risk class defines severity, gates define prerequisites.

Evaluator: Check that each scope has a corresponding risk class mapping and gate checklist. Verify that the most restrictive scope (live) has the most gates.

Source: hermes-perm-audit-001, GPT architect + Claude Code repo-reader convergence.
