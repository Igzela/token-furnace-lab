# F-0003: Runtime Artifact Secret Leakage Risk

Failure: Audit log captures unsanitized "reason" fields. Reliability monitor captures unsanitized command output including potential path secrets.

Impact: Medium. Secrets provided in reason text persist in audit.jsonl on disk. Tailscale URLs with path secrets may appear in reliability reports.

Root cause: `sanitize_text` truncates but does not scrub secrets. `sensitive_output_included` flag is set but output is not actually redacted.

Recovery: Extend sanitize_text to detect and scrub secret patterns. Redact tailscale URLs in reliability reports before storage.

Source: hermes-perm-audit-001, Codex risk reviewer + GPT architect convergence
