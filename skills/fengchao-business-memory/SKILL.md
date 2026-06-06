---
name: fengchao-business-memory
description: Use when a project using FengChaoSkills needs memory routing, plan capture, conversation memory capture, or completed-development memory maintenance.
metadata:
  short-description: Maintain business memory after real development
---

# FengChao Business Memory

FengChaoSkills maintains a traceable business memory system for long-lived projects. FengWang is the routing entry that helps a fresh AI conversation find the smallest relevant set of project memories.

## Memory Modes

- **New request routing**: read `fengwang/FENGWANG.md` and use `fengchao.py fengwang --query "..."` to find related context.
- **Plan capture**: after a final plan is produced, write `plan-records/`; do not write changelog or business truth.
- **Conversation capture**: when the user explains durable business context, terms, preferences, or rejected options, write `conversation-records/`; do not promote it to current truth by default.
- **Development completion**: after real delivered changes, write `task-records/`, `changelog/`, update `fengwang/`, and update `business-context/` only for stable landed facts.

## Guardrails

- Plan records and conversation records are historical/contextual memory, not current business truth.
- Only confirmed or implemented facts enter `business-context/`.
- Do not archive complete conversations by default; store extracted summaries.
- Git diff is supporting evidence, not the source of business meaning.

## Workflow

1. Read `references/lifecycle.md` for mode selection.
2. Read the mode-specific reference: FengWang, plan, conversation, or task/changelog.
3. Use `scripts/fengchao.py` commands when deterministic files are enough.
4. Update only the memory layer that matches the mode.
5. Run `scripts/fengchao.py check` before final response after any memory write.

## CLI

From the target project root:

```bash
python path/to/fengchao.py init --project-name "Project Name"
python path/to/fengchao.py fengwang --query "user request"
python path/to/fengchao.py plan --title "..." --goal "..." --plan "..."
python path/to/fengchao.py conversation --title "..." --summary "..."
python path/to/fengchao.py maintain --title "..." --summary "..." --implementation "..."
python path/to/fengchao.py check
python path/to/fengchao.py inspect
```

The CLI is a guardrail, not a replacement for judgment. The primary source for business memory is the completed task conversation and confirmed implementation; git diff is only supporting evidence.

## Reference Map

- `references/lifecycle.md`: trigger gate, completion sequence, privacy defaults.
- `references/fengwang-system.md`: FengWang routing model.
- `references/plan-record-system.md`: plan capture rules.
- `references/conversation-record-system.md`: conversation memory rules.
- `references/memory-promotion-rules.md`: promotion and conflict rules.
- `references/context-system.md`: progressive `business-context/` structure.
- `references/task-record-system.md`: immutable task-record model and template.
- `references/changelog-system.md`: changelog entry and progressive changelog index.
- `references/routing-rules.md`: how to decide which context files to update.
- `references/templates.md`: concise manual templates.
