# Reusable Prompt: Hermes Permission Architecture Audit

Use for: Auditing permission boundaries in hermes-gateway-lab or similar execution gateway systems.

Prompt:
```
You are auditing the permission architecture of an execution gateway system.

Focus on:
1. Scope model: What scopes exist? Which are enabled?
2. Risk classes: What classes exist? Which are disabled?
3. Gate checklist: What checks are required before live execution?
4. Approval flow: Who can approve? What channels are valid?
5. Kill switch: Can execution be globally disabled? Is it tested?

For each area, classify findings as:
- Grounded: directly supported by code or docs
- Inferred: reasonable implication, needs verification
- Unknown: insufficient evidence

Output: Architecture risks, missing controls, recommended changes.
```

Source: hermes-perm-audit-001, GPT architect prompt
