# FengChaoSkills

FengChaoSkills is an open-source, multi-agent business-memory toolkit for long-lived software projects.

It is not a generic diff-to-changelog generator. Its core job is to help AI agents route through project memory, preserve business intent, capture plans and durable user explanations, and maintain evidence from real development tasks so future conversations can recover context without the user re-explaining the business.

## Supported Agent Surfaces

- Claude Code: `adapters/claude-code/CLAUDE.md.snippet`
- Codex: `adapters/codex/AGENTS.md.snippet`
- Cursor: `adapters/cursor/fengchao.mdc`
- OpenCode: `adapters/opencode/opencode.json.snippet`

## Trigger Boundary

Use FengWang routing at the start of a new project conversation.

Capture final plans in `plan-records/`. Capture durable user explanations in `conversation-records/`. Only real development completion writes `task-records/` and `changelog/`.

## Quick Start

From a target project root:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py init --project-name "Project Name"
```

`init` creates the project memory folders, writes the OpenCode/Codex/Claude/Cursor rule files, and installs project-local skill copies at:

```text
.opencode/skills/fengchao-business-memory/
.claude/skills/fengchao-business-memory/
.cursor/skills/fengchao-business-memory/
.codex/skills/fengchao-business-memory/
.agents/skills/fengchao-business-memory/
```

After a real development task:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py maintain \
  --title "设计单两级审核" \
  --domain "design" \
  --summary "用户要求把设计单审核从单级改成主管和经理两级。" \
  --business-change "设计单最终通过必须经过主管审核和经理审核。" \
  --implementation "新增审核阶段字段并调整审核状态机。" \
  --evidence "review flow implementation" \
  --validation "compile passed"
```

Capture a final plan:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py plan \
  --title "审核流程优化计划" \
  --domain "design" \
  --goal "用户希望调整审核流程。" \
  --plan "把审核拆成主管和经理两级。"
```

Capture durable conversation context:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py conversation \
  --title "审核角色业务解释" \
  --domain "design" \
  --summary "用户解释主管和经理审核的业务边界。" \
  --term "主管=main 岗位，负责一审"
```

Route a new request through FengWang:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py fengwang \
  --query "我要改设计单审核"
```

Validate:

```bash
python /path/to/FengChaoSkills/skills/fengchao-business-memory/scripts/fengchao.py check
```

## Project Memory Model

- `task-records/`: immutable records of completed development tasks.
- `business-context/`: current progressive business context for fresh AI conversations.
- `changelog/`: implementation history with a progressive index.
- `plan-records/`: final plans and proposal history, not current business truth.
- `conversation-records/`: extracted user business explanations, terms, preferences, and rejected options.
- `fengwang/`: unified routing entry and memory map.

By default, FengChaoSkills stores extracted summaries only, not full conversations.
