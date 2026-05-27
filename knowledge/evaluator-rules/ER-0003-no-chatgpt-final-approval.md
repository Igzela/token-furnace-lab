# ER-0003: No ChatGPT Final Approval

Rule: ChatGPT cannot be the final approver for local execution. Approval source must be validated at runtime to reject ChatGPT-only approval.

Test: Create task with ChatGPT-only approval, attempt execution. Assert denial.

Severity: High
Source: hermes-perm-audit-001, DR-0003
