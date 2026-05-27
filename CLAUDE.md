# Token Furnace Lab - Claude Code Instructions

## 项目概述

这是一个 AI agent 实验平台，故意制造高 token 消耗但必须产出可检查资产。

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
