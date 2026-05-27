# Reusable Prompt: Repo Reader Permission Surface

Use for: Generating a filesystem inventory and reading permission-relevant files from a target repo.

Prompt:
```
You are the repo reader.

Task:
1. Generate a filesystem inventory (find . -type f)
2. Filter for permission-relevant files (*.py, *.sh, *.md, *.json, *.yaml)
3. Read key files: AGENTS.md, safety docs, execution scripts, approval queue
4. For each file, note: reason for reading, exists status, key observations

Focus on permission-relevant surfaces:
- Scope definitions
- Risk classifications
- Gate checklists
- Approval flows
- Secret handling
- Recovery/rollback

Output: File inventory table, permission-relevant surfaces, grounded suggestions, unknowns.
No-write confirmation: State that no files were modified.
```

Source: hermes-perm-audit-001, Claude Code repo-reader prompt
