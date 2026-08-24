# Lifecycle

## Mode Decision

Choose one mode per situation:

- **FengWang routing**: a new user request arrives in a project that has FengChao memory.
- **Plan capture**: Plan mode or proposal work produced a final plan.
- **Conversation capture**: the user explained durable business context, terminology, preferences, constraints, or rejected options.
- **Fact registration**: the user asserted a project fact with certainty — an entry point, a config value, a term anchor, a code convention. Rides on conversation capture via `--confirmed-fact`.
- **Development completion**: a real development task produced delivered project changes.

Only development completion writes `task-records/` and `changelog/`.

## Non-Development Modes

- Plan capture writes `plan-records/` and updates `memory-map.md`.
- Conversation capture writes `conversation-records/` and updates `memory-map.md`.
- Neither mode writes `business-context/` unless the user explicitly confirms the information is current business truth.
- Fact registration is exactly that exception: `--confirmed-fact` writes `business-context/project-facts.md`, because the user asserting a fact **is** the explicit confirmation. It stays gated on `extraction-quality.md` section 5 (strict by default) and on asking the user before writing. Facts merge validate-first: a bad `--confirmed-fact` format or an unknown `--retire-fact` name fails the whole command with no partial writes, not even the conversation record.

## Development Completion: Two Tiers (lite / full)

One-sentence tier test（一句话判定标准）:

> **半年后的新会话是否需要知道这次改动的"为什么"？** 需要 → full；不需要（纯修复/重构/杂务）→ lite。
> (Will a fresh session six months from now need the "why" of this change? Yes → full; no → lite.)

- **lite** (no `--business-change`): writes one changelog entry + one memory-map row only. No task record, no business-context change. This is the default for bugfixes, refactors, and chores — keep the memory system noise-free.
- **full** (`--business-change` provided): immutable task record + changelog + semantic merge into `business-context/` + memory-map rows. Requires `--change-kind added|modified|removed`, a stable `--rule-name`, and ideally a `--scenario`.
- Escape hatch: `--with-task-record` forces a task record for a lite delivery (e.g. a major refactor worth documenting without business change).

## Development Completion Flow (full tier)

1. Gather evidence from the current conversation, final implementation, changed files, and verification output.
2. Run the five-question self-check and change-kind determination in `references/extraction-quality.md` (mandatory).
3. Run `maintain` — it validates the semantic merge first and fails whole (no partial writes) on `rule_already_exists` / `rule_not_found`.
4. The CLI writes the task record, changelog, index rows, merged domain file, and memory-map rows, then re-checks links.
5. Run `fengchao.py check` before the final response.
6. In the final response, mention the memory artifacts updated and any verification gap.

## Source Priority

1. Final conversation outcome and user-confirmed intent.
2. Implemented code and tests.
3. Git diff and file list.
4. Existing business context and historical records.

Diff is evidence, not the memory source. The business memory should explain why the change exists and what business fact is now true.

## Privacy Default

Store only extracted summaries. Do not archive complete conversations by default. Include short user wording only when it is necessary to preserve a business term or rule.
