# First Experiment: Hermes Gateway Lab 权限审计

## Objective
审计 hermes-gateway-lab 的 agent 权限边界，并提出 3 个可执行改进

## Models
1. **GPT**: 架构审计
2. **Claude Code**: repo 读取与实现建议
3. **Codex**: 代码级风险审查
4. **Judge**: 比较三份输出，判断谁更可靠

## Task Definition
```
审计 hermes-gateway-lab 的 agent 权限边界：
1. 识别所有权限控制点
2. 检查权限提升风险
3. 评估权限隔离效果
4. 提出 3 个可执行改进建议
```

## Verification Criteria
- [ ] 识别出至少 5 个权限控制点
- [ ] 发现至少 1 个潜在风险
- [ ] 提出的建议可直接实施
- [ ] 三个模型的结论可交叉验证

## Expected Outputs
- [ ] 3 份独立审计报告
- [ ] 1 份交叉审计报告
- [ ] 1 份 wiki note
- [ ] 1 条新 evaluator rule
- [ ] 1 个 next experiment proposal

## Run Directory
```
runs/2026-05-27-hermes-perm-audit-001/
├── task.md
├── model_outputs/
│   ├── gpt-arch-audit.md
│   ├── claude-impl-suggestions.md
│   └── codex-risk-review.md
├── traces/
│   ├── gpt-trace.json
│   ├── claude-trace.json
│   └── codex-trace.json
├── cross_audit/
│   └── judge-report.md
├── cost_estimate.md
├── failure_analysis.md
├── distilled_wiki_notes/
│   └── hermes-perm-boundaries.md
├── decision_record.md
└── next_experiment.md
```
