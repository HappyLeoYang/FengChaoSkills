---
name: fengchao-business-memory
description: Use when a project using FengChaoSkills needs memory routing, plan capture, conversation memory capture, or completed-development memory maintenance.
metadata:
  short-description: Maintain business memory after real development
---

# FengChao Business Memory

FengChaoSkills maintains a traceable business memory system for long-lived projects. FengWang is the routing entry that helps a fresh AI conversation find the smallest relevant set of project memories.

The default installed layout keeps the tool at `.fengchao/` (single install point) and all memory under one memory root (default `fengchao/`, see `.fengchao/config.yaml` key `memory_root`). Legacy layouts (six directories at the project root) remain readable; `migrate` converts them.

## Memory Modes

- **New request routing**: read `<memory-root>/FENGWANG.md` and use `fengchao.py fengwang --query "..."` to find related context. Read the top 3 results first; output is byte-budgeted.
- **Plan capture**: after a final plan is produced, write `plan-records/`; do not write changelog or business truth. When the plan lands later, backfill with `fengchao.py plan-status <record> --status implemented --link <task-record>`.
- **Conversation capture**: when the user explains durable business context, terms, preferences, or rejected options, write `conversation-records/`; do not promote it to current truth by default.
- **Development completion**: after real delivered changes, run `maintain`. Two tiers (lite/full) — see Workflow step 3.

## Guardrails

- Plan records and conversation records are historical/contextual memory, not current business truth.
- Only confirmed or implemented facts enter `business-context/`, and only through `maintain --business-change` semantic merge (added/modified/removed). Never append rules to domain files by hand.
- One rule name is a stable key: at any moment a domain file holds at most one active entry per rule.
- Do not archive complete conversations by default; store extracted summaries.
- Git diff is supporting evidence, not the source of business meaning.

## Workflow

1. Read `references/lifecycle.md` for mode selection.
2. Read the mode-specific reference: FengWang, plan, conversation, or task/changelog.
3. **Before any `maintain` write (mandatory)**: run the five-question self-check and the change-kind determination from `references/extraction-quality.md` —
   a. Answer the five questions (real motive, rule from→to, terms, rejections, what future sessions stop re-asking).
   b. Decide the tier: business meaning → full (`--business-change` + `--change-kind` + `--rule-name` + `--scenario`); pure fix/refactor/chore → lite (omit `--business-change`).
   c. For full tier: read the target domain file's current-rules section first, then pick added/modified/removed and reuse the existing rule name for modified/removed.
4. Use `scripts/fengchao.py` commands; update only the memory layer that matches the mode.
5. Run `scripts/fengchao.py check` before the final response after any memory write (full-tier maintain re-checks links automatically).

## CLI

From the target project root (installed projects: `python3 .fengchao/skill/scripts/fengchao.py ...`):

```bash
python3 .fengchao/skill/scripts/fengchao.py fengwang --query "user request"
python3 .fengchao/skill/scripts/fengchao.py plan --title "..." --goal "..." --plan "..."
python3 .fengchao/skill/scripts/fengchao.py conversation --title "..." --summary "..." --term "..." --rejected "..."
# lite delivery (no business rule change):
python3 .fengchao/skill/scripts/fengchao.py maintain --title "..." --summary "..." --implementation "..."
# full delivery (business rule changed):
python3 .fengchao/skill/scripts/fengchao.py maintain --title "..." --summary "..." --implementation "..." \
  --business-change "..." --change-kind added|modified|removed --rule-name "..." --scenario "..."
python3 .fengchao/skill/scripts/fengchao.py check          # --warn / --strict / --format json
python3 .fengchao/skill/scripts/fengchao.py status         # health overview, --format json
```

Lifecycle and maintenance commands: `enable` / `disable` / `uninstall` / `upgrade` / `migrate` / `archive --before` / `compact` / `plan-status` / `doctor`.

The CLI is a guardrail, not a replacement for judgment. The primary source for business memory is the completed task conversation and confirmed implementation; git diff is only supporting evidence.

## Reference Map

- `references/lifecycle.md`: trigger gate, lite/full tiers, completion sequence, privacy defaults.
- `references/extraction-quality.md`: five-question self-check, change-kind determination, anti-patterns, good/bad examples. **Mandatory before maintain.**
- `references/fengwang-system.md`: FengWang routing model.
- `references/plan-record-system.md`: plan capture rules.
- `references/conversation-record-system.md`: conversation memory rules.
- `references/memory-promotion-rules.md`: promotion and conflict rules.
- `references/context-system.md`: progressive `business-context/` structure and rule-entry format.
- `references/task-record-system.md`: immutable task-record model and template.
- `references/changelog-system.md`: changelog entry and progressive changelog index.
- `references/routing-rules.md`: how to decide which context files to update.
- `references/templates.md`: concise manual templates.
