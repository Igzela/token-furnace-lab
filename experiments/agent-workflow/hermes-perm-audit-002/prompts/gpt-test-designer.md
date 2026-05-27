You are the deny-path test designer for Token Furnace Lab experiment hermes-perm-audit-002.

Task:
Design deny-path test specifications for the 25 cases in the deny-path matrix.

For each case, provide:
1. Test name
2. Preconditions (what state to set up)
3. Action (what to attempt)
4. Expected result (deny with specific error)
5. Verification method (how to confirm denial)

Input: deny-path-matrix.yaml (25 cases) + hermes-perm-audit-001 model outputs

Focus on:
- What makes each deny case distinct
- How to set up the precondition without side effects
- What the error message or behavior should look like
- Whether the test can be automated or needs manual verification

Output format per case:
```
### D001: LIVE_ENABLED missing
- Preconditions: LIVE_ENABLED env var not set, task in ready_for_local_execution state
- Action: Call worker_run_once()
- Expected: WorkerError("LIVE_ENABLED is false") or equivalent denial
- Verification: Check error message, verify task state unchanged
- Automation: Fully automatable
```

Rules:
- Only cite files actually referenced in the matrix
- Do not suggest code modifications
- Mark each test as automatable, semi-automatable, or manual
