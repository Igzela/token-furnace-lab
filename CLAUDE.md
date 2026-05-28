# Token Furnace Lab - Claude Code Instructions

## 项目概述

这是一个 AI agent 实验平台，故意制造高 token 消耗但必须产出可检查资产。核心问题：大量 token 在什么条件下会变成真实生产力，而不是噪声？

## 当前阶段

Active Research — 个人研究项目，迭代中，无外部用户。

## 新 session 启动顺序

所有 Claude Code、Codex 或其他 coding agent 必须先读：

1. `docs/SESSION_START_HERE.md`
2. `AGENTS.md`
3. `docs/runs/token-furnace-current-state.md`
4. `knowledge/wiki/small-dc-link-foc-technical-route.md`
5. 最新 active run 的 `status.md`、`task.md`、`model_outputs/` 和 `synthesis/`

如果这些文件、README、最近 git log 互相冲突，先修文档，不要直接推进实验。

## 非目标（Out of Scope）

- 不是生产部署的 AI agent — 这是实验室/研究项目
- 不自动生成用户文档或 README
- 不引入 CI/CD 或自动发布流程
- 不做线上用户服务
- 不引入重型框架或不必要依赖

## 技术栈

- **语言**: Python 3.10+, Bash 脚本
- **依赖**: 极简主义，仅 PyYAML（不引入重型框架）
- **AI 模型**: Claude (via claude code), GPT (via API), 其他 LLM
- **工具**: 自写脚本，不使用 CI/CD 平台

## 外部依赖

- Claude Code CLI（主要 agent 执行环境）
- OpenAI API（用于 GPT 交叉验证）
- Obsidian（知识沉淀的阅读端，不通过代码集成）

## 核心规则

1. **每次实验必须生成结构化产物**
   - task.md
   - model_outputs/
   - traces/
   - cost_estimate.md
   - failure_analysis.md
   - distilled_wiki_notes/
   - decision_record.md
   - next_experiment.md

2. **多模型交叉审计**
   - 同一任务至少 2 个模型执行
   - 第三个模型做差异审查
   - 记录每个模型的 token 消耗

3. **知识沉淀强制结构化**
   ```
   Observation: [观察到什么]
   Rule candidate: [建议的规则]
   Evaluator: [如何验证]
   ```

4. **实验目录命名规范**
   ```
   runs/YYYY-MM-DD-<experiment-type>-<id>/
   ```

## 可用 Agent

- security-reviewer: 安全审计
- code-reviewer: 代码审查
- Explore: 快速代码探索
- Plan: 实现方案设计

## 当前活跃实验

- `hermes-perm-audit-001~008` — 权限审计系列（Phase 1 完成）
- `small-dc-link-foc-derivation` — 小直流链路 FOC 推导
  - derivation-001: ripple model (90/100 PASS)
  - derivation-002: energy balance (85/100 PASS_WITH_NOTES)
  - derivation-003: FOC voltage envelope (82/100 PASS_WITH_NOTES)
  - derivation-004: APD sizing (78/100 PASS_WITH_TWO_CORRECTIONS)
  - derivation-005: joint simulation (GPT final PASS_WITH_NOTES 86/100 — corrected model conditionally accepted; 300W requires high nominal bus and high APD decoupling)
  - phase-a-001: FOC baseline design (COMPLETE)
  - phase-e-001: runtime fault recovery model (72/100 PASS_WITH_NOTES — 12 states, 19 fault codes, GPT caught 7 major corrections)
  - phase-a-004: fixed-point CPU/RAM budget (PASS_WITH_NOTES — corrected ISR to 6000 cycles, two-layer observer, fast ISR 44% utilization)
  - 详细进度见 `knowledge/wiki/small-dc-link-foc-technical-route.md`
- `mcp-bridge-boundary-audit` — MCP 桥接边界审计
- `orchestration-001~004` — 多 agent 编排系列
  - orchestration-001: basic pipeline (82/100 PASS)
  - orchestration-002: mock execution (100/100 PASS)
  - orchestration-003: schema enforcement + failure injection (10/10 PASS)
  - orchestration-004: real multi-model cross-audit (77/100 PASS_WITH_NOTES — Claude 78 + GPT 76, GPT found 2 additional HIGH blocking findings)
  - orchestration-005: review fusion + multi-reviewer gate (COMPLETE — findings union, blocking override, disagreement tracking)
  - orchestration-006: fused repair execution benchmark (COMPLETE — closed-loop verified, ACCEPT 92/90, 2 repair rounds)
  - orchestration-007: multi-worktree parallel dispatch (COMPLETE — 3/3 subproblems parallel, artifacts collected, ~30s wall time)
  - orchestration-008: confidence & escalation calibration (COMPLETE/PASS — 9/9 calibration cases, 3/3 pipeline tests, 5-component confidence scoring, decision policy, timeout classifier)
  - orchestration-009: outcome memory + policy tuning loop (COMPLETE/PASS — 10 runs ingested, 13 lessons, 8 policy suggestions, 10 active policies, self-modification gate)
  - orchestration-010: safe policy application engine (COMPLETE/PASS — policy patches, config layer, regression tests 4/4, repeat failure detection, policy effectiveness measurement)
  - orchestration-011: adaptive task routing (COMPLETE/PASS — 3-layer router: task_profiler + memory_matcher + routing_decision, 8 task types, 7 strategies, routing outcome tracking)
  - orchestration-012: self-evaluation benchmark (COMPLETE/PASS — 8 cases, adaptive vs baseline: +13.2 score, -83% missed blocking, 88% route accuracy, 0 false accepts)

### Key Decisions (FOC derivation series)

- **Solution fork**: Path A — keep 22µF DC-link + add APD (Active Power Decoupling)
- **APD**: 16µF/500V H-bridge, 90% decoupling → 300W achievable at 3000-4000rpm remains the last accepted result; derivation-005 provides a stronger local PASS candidate but needs GPT final verification before sealing.
- **Motor parameter**: ψ_f ≤ 0.103 for 300V/4000rpm (revised from 0.15 to 0.08)
- **GPT communication**: via Chrome DevTools MCP (`fill` + `press_key Enter`, not `type_text`)
- **GPT role**: Cross-verification of derivations; GPT caught 3 critical formula/numerical errors and identified derivation-005 APD/model bugs
- **derivation-005 final review**: corrected electrical-power balance and APD sanity checks passed GPT final verification with notes; next recommended experiment is APD branch current / inductor / switching-device sizing
- **Two-layer observer**: SMO at 5kHz (separate task), angle prediction at 10kHz (in ISR). GPT caught ISR budget error (6000 cycles, not 15000). Fast ISR 44% utilization, well under 70% target.

### Key Decisions (Orchestration series)

- **Gate priority rules**: Validator FAIL > Evidence errors > Blocking findings > Score > Verdict (validated with 10/10 failure-injection tests)
- **JSON-block parsing**: Agents output structured JSON in markdown; validators extract from JSON blocks first, then fall back to markdown regex
- **Cross-audit delta**: GPT found 2 HIGH blocking findings Claude missed (universal hard-fault rules, CONTROLLED_COAST ambiguity) — cross-audit adds real value
- **Next experiment**: orchestration-009 — Candidate TBD (see current-state index)
- **Cascade pattern**: Fixing one dangling transition target exposes related ones in the same sequence; re-review catches defects the original review missed
- **Closed-loop verified**: review_fusion → repair → re-review → fusion → ACCEPT works in 2 rounds
- **Confidence calibration**: 5-component weighted scoring; repeated LOW findings are informational, not blocking; timeout classifier defaults to REVIEW for ambiguous patterns
- **Adaptive learning**: outcome_memory.jsonl stores machine-readable run history; orchestrator_learn.py extracts lessons and generates policy suggestions; system can auto-tighten but never auto-loosen without human approval

## 自主推进协议

负责推进本仓库的 coding agent 可以自主把研究任务推进到可交接提交，不需要每一步都等待人工指令。自主权限覆盖 run 创建、模型输出整理、交叉审计、synthesis、wiki 沉淀、validator 修复、commit 和 push；不覆盖生产部署、CI/CD 发布、重型框架或外部自动发布。

每个 session 必须执行：

1. 先运行 `git status --short --branch`，识别未提交或未跟踪的 run，不能覆盖其他 agent 的工作。
2. 读取启动文档和最新 run 的 `status.md`、`run.yaml`、`task.md`、`model_outputs/`、`synthesis/`。
3. 如果已有 in-progress run，优先完成它的 next step；若不处理，明确保持 untouched，不开同主题竞争 run。
4. 如果最新 run 已关闭，从 decision record、current-state index 或 wiki 的 next step 选择下一个实验。
5. 接受任何 finding 前必须有 synthesis 和 cross-audit 记录。
6. 对变更过的 run 执行 `python3 scripts/validate_run.py runs/<experiment>/<timestamp>/`，并在 commit 前执行 `python3 scripts/check_agent_handoff.py`。
7. 状态、accepted finding、active run 或 next experiment 变化时，同步更新入口文档、current-state index、相关 wiki、run metadata 和 synthesis。
8. commit message 使用英文；当工作树只包含本 session 预期变更时 push 当前分支。
9. final report 留下 latest commit、verdict、validation、remaining risks、next experiment。

## 决策与知识库

- 架构决策: `knowledge/decisions/`
- 失败分析: `knowledge/failures/`
- 可复用 Prompt: `knowledge/reusable-prompts/`
- 评估规则: `knowledge/evaluator-rules/`
- Wiki 笔记: `knowledge/wiki/`

## 脚本验证

- 修改 `scripts/` 后，用 `python scripts/validate_run.py runs/<latest>` 验证
- 新建 run 后，必须运行 `scripts/validate_run.py` 确保结构合规
- 每次 commit 前运行 `python3 scripts/check_agent_handoff.py`

## Commit 规范

- 英文，祈使句，首字母大写
- 格式: `<Verb> <what> [optional context]`
- 示例: `Add GPT final verification for derivation-002`

## 运行环境

- 本地运行，无服务器、无部署
- 所有产物存储在 `runs/` 和 `knowledge/`
- 不涉及外部服务的生产环境

## 路径作用域

- `runs/` - 实验运行记录，需要完整审计
- `knowledge/` - 知识沉淀，需要结构化验证
- `scripts/` - 自动化脚本，可以自由修改
- `config/` - 配置文件，修改前需要确认

## 实验流程

1. 定义任务 (task.md)
2. 选择模型/agent 组合
3. 执行并记录 traces
4. 生成 cost_estimate.md
5. 多模型交叉审计
6. 知识沉淀 (wiki + rules + evaluator)
7. 生成 next_experiment.md

## 文档维护规则

每次 commit 前，如果 active run、分支、状态、验证结果、accepted finding 或 next experiment 发生变化，必须同步更新：

- `docs/SESSION_START_HERE.md`
- `docs/runs/token-furnace-current-state.md`
- `knowledge/wiki/small-dc-link-foc-technical-route.md`
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- active run 的 `status.md`、`run.yaml`、`synthesis/`

如果不需要更新文档，在 completion report 中说明原因。新 session 必须能只靠文档接手。
