# Risk Rubric

Score 0-5 for each dimension.

## 1. Finding Groundedness (0-5)
- 0: All findings speculative
- 3: Mix of grounded and inferred
- 5: All findings cite specific files/lines

## 2. Risk Severity Accuracy (0-5)
- 0: Severity ratings arbitrary
- 3: Severity roughly correct
- 5: Severity justified with exploitability/impact analysis

## 3. Coverage (0-5)
- 0: Misses obvious risks
- 3: Covers major risks, misses edge cases
- 5: Comprehensive coverage including edge cases

## 4. Patch Quality (0-5)
- 0: No patches suggested
- 3: Patches reasonable but untested
- 5: Minimal, targeted patches with rationale

## 5. False Positive Rate (0-5)
- 0: High false positive rate
- 3: Some false positives, acknowledged
- 5: Clean findings, false positives explicitly separated

## Pass Threshold
Total >= 15/25 and no dimension = 0
