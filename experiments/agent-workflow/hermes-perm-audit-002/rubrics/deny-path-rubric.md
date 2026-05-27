# Deny-Path Audit Rubric

## Dimensions (0-5 each)

### 1. Coverage Completeness
- 0: No cases mapped
- 1: <25% cases have code references
- 2: 25-50% cases mapped
- 3: 50-75% cases mapped
- 4: 75-90% cases mapped
- 5: All 25 cases have code references

### 2. Evidence Quality
- 0: No evidence
- 1: Only inferred evidence
- 2: Mix of inferred and grounded
- 3: Mostly grounded with file/line citations
- 4: All grounded, some with test specifications
- 5: All grounded with executable test specs

### 3. Gap Identification
- 0: No gaps identified
- 1: Some gaps noted but not categorized
- 2: Gaps categorized by severity
- 3: Gaps with root cause analysis
- 4: Gaps with prioritized remediation path
- 5: Gaps with complete deny-path test plan

### 4. Bypass Analysis
- 0: No bypass analysis
- 1: Mentions bypasses exist
- 2: Lists bypass paths
- 3: Analyzes bypass conditions
- 4: Proposes bypass prevention
- 5: Complete bypass prevention with test coverage

### 5. Matrix Integrity
- 0: Matrix not updated
- 1: Matrix partially updated
- 2: All cases have status
- 3: All cases have severity
- 4: All cases have evidence references
- 5: Matrix is machine-verifiable

## Scoring
- Pass: >= 15/25
- Pass with notes: 12-14/25
- Fail: < 12/25

## Critical Gate Override
If D001, D005, D006, D018, or D019 are marked NO_COVERAGE, overall result is FAIL regardless of score.
