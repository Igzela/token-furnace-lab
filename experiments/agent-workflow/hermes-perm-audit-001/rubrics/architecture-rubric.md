# Architecture Rubric

Score 0-5 for each dimension.

## 1. Permission Model Clarity (0-5)
- 0: No identifiable permission model
- 3: Implicit permissions, scattered across files
- 5: Explicit, documented, enforced permission model

## 2. Read/Write Separation (0-5)
- 0: No separation, any agent can write anywhere
- 3: Some separation, but bypassable
- 5: Strict separation with enforcement

## 3. Dangerous Operation Controls (0-5)
- 0: No controls on destructive ops
- 3: Some controls, but incomplete
- 5: Comprehensive controls with dry-run/preview

## 4. Rollback Safety (0-5)
- 0: No rollback mechanism
- 3: Manual rollback possible but risky
- 5: Safe, tested rollback with audit trail

## 5. Auditability (0-5)
- 0: No logging or traceability
- 3: Partial logging
- 5: Full audit trail of all permission-relevant actions

## Pass Threshold
Total >= 15/25 and no dimension = 0
