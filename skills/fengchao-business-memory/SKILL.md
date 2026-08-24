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
- **Fact registration**: when the user asserts a project fact **with certainty** (entry point, config value, term anchor, code convention), register it with `conversation --confirmed-fact` in the same call. Gate on `references/extraction-quality.md` section 5 — strict by default, and ask the user before writing.
- **Development completion**: after real delivered changes, run `maintain`. Two tiers (lite/full) — see Workflow step 3.

## Guardrails

- Plan records and conversation records are historical/contextual memory, not current business truth.
- Only confirmed or implemented facts enter `business-context/`: business rules through `maintain --business-change` semantic merge (added/modified/removed), user-asserted project facts through `conversation --confirmed-fact`. Never append entries to managed sections by hand.
- One rule name — and one fact name — is a stable key: at any moment there is at most one active entry per name.
- A fact the AI inferred from source code is **not** a confirmed fact. It stays in the "unverified" section (or `--promote candidate`) until the user confirms it. Code is supporting evidence, never the source of business meaning.
- Registered facts are clues, not guarantees: nothing re-verifies them against the codebase. When a fact contradicts the code, the code wins — say so and offer to update the registration.
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
# register facts the user asserted with certainty (name is a stable key; same name overwrites the value):
python3 .fengchao/skill/scripts/fengchao.py conversation --title "..." --summary "..." \
  --confirmed-fact "设计单提交审核入口=POST /liangang/workorder/submitReview" --fact-kind entry-point
# retire a fact that is void (not merely changed — a changed value is just re-registered):
python3 .fengchao/skill/scripts/fengchao.py conversation --title "..." --summary "..." --retire-fact "旧入口名"
# lite delivery (no business rule change):
python3 .fengchao/skill/scripts/fengchao.py maintain --title "..." --summary "..." --implementation "..."
# full delivery (business rule changed):
python3 .fengchao/skill/scripts/fengchao.py maintain --title "..." --summary "..." --implementation "..." \
  --business-change "..." --change-kind added|modified|removed --rule-name "..." --scenario "..."
# link back to the source record — bare name, memory-root relative, or project-root relative all work:
python3 .fengchao/skill/scripts/fengchao.py maintain ... --from-conversation "2026-01-01_001_review-roles"
python3 .fengchao/skill/scripts/fengchao.py check          # --warn / --strict / --format json
python3 .fengchao/skill/scripts/fengchao.py status         # health overview, --format json
```

Lifecycle and maintenance commands: `enable` / `disable` / `uninstall` / `upgrade` / `migrate` / `archive --before` / `compact` / `plan-status` / `doctor`.

The CLI is a guardrail, not a replacement for judgment. The primary source for business memory is the completed task conversation and confirmed implementation; git diff is only supporting evidence.

## Reference Map

- `references/lifecycle.md`: trigger gate, lite/full tiers, completion sequence, privacy defaults.
- `references/extraction-quality.md`: five-question self-check, change-kind determination, anti-patterns, good/bad examples, and the certainty-signal checklist for fact registration. **Mandatory before maintain and before `--confirmed-fact`.**
- `references/fengwang-system.md`: FengWang routing model.
- `references/plan-record-system.md`: plan capture rules.
- `references/conversation-record-system.md`: conversation memory rules.
- `references/memory-promotion-rules.md`: promotion and conflict rules.
- `references/context-system.md`: progressive `business-context/` structure, rule-entry format, and `project-facts.md`.
- `references/task-record-system.md`: immutable task-record model and template.
- `references/changelog-system.md`: changelog entry and progressive changelog index.
- `references/routing-rules.md`: how to decide which context files to update.
- `references/templates.md`: concise manual templates.
