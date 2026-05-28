# Token Furnace Lab

AI Agent 系统压测与知识蒸馏实验室

**New coding-agent sessions should start with [docs/SESSION_START_HERE.md](docs/SESSION_START_HERE.md), then [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md).**

Responsible coding agents may autonomously advance research tasks from run creation to committed handoff. They must update the active run status, current-state index, and knowledge wiki after every commit-sized experiment change, then run `python3 scripts/check_agent_handoff.py` before commit.

## Goal

构建一个高 token 消耗但高沉淀率的 AI agent 实验系统，用于测试、比较、压测和改进多模型、多工具、多知识库协作流程。

## Core Question

大量 token 在什么条件下会变成真实生产力，而不是噪声？

## 高效烧 token 公式

```
高 token 输入
+ 强约束任务
+ 可验证输出
+ 多模型交叉审计
+ 知识沉淀机制
= 有价值的烧 token
```

## 目录结构

```
token-furnace-lab/
├── runs/                    # 实验运行记录
├── knowledge/               # 知识沉淀
│   ├── raw/                 # 原始笔记
│   ├── wiki/                # 结构化 wiki
│   ├── decisions/           # 决策记录
│   ├── failures/            # 失败案例
│   ├── reusable-prompts/    # 可复用 prompt
│   └── evaluator-rules/     # 评估规则
├── experiments/             # 实验定义
│   ├── model-comparison/    # 模型对比
│   ├── agent-workflow/      # Agent 工作流
│   ├── prompt-compression/  # Prompt 压缩
│   ├── long-context-memory/ # 长上下文记忆
│   └── paper-to-algorithm/  # 论文算法提取
├── scripts/                 # 自动化脚本
├── config/                  # 配置文件
└── docs/                    # 文档
```

## Inputs

- GitHub repos
- Obsidian/wiki notes
- PDF papers
- Agent traces
- Prompt files
- Tool configs
- Experiment logs

## Outputs

- Benchmark reports
- Model capability matrix
- Reusable prompts
- Agent rules
- Wiki notes
- Failure taxonomy
- Decision records
- Next experiment plans

## Main Experiments

1. Same task, different model
2. Same repo, different agent workflow
3. Same paper corpus, different extraction method
4. Same coding issue, planner-executor vs single-agent
5. Long-context full review vs retrieval-based review
6. Human-in-loop vs auto-agent execution

## Metrics

- Success rate
- Correction count
- Hallucination count
- Token cost
- Human review time
- Artifact usefulness
- Repeatability
- Repo safety

## 四层架构

### Layer 1: Token Furnace Runner
制造任务、调用不同 agent、记录过程

### Layer 2: Agent Capability Benchmark
测试不同 AI 工具适合干什么

### Layer 3: Knowledge Distillation Pipeline
把烧掉的 token 变成长期资产

### Layer 4: Advisor/Executor Architecture
Planner → Executor → Advisor → Critic → Archivist → Judge
