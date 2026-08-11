# Task Records

`task-records/` stores immutable records of completed development tasks. It preserves why a business rule changed and how it was implemented.

## Required Fields

- Title.
- Record time.
- Domain.
- Privacy policy: summary-only by default.
- Link to changelog.
- User business intent.
- Final confirmed business rules.
- Final implementation plan actually delivered.
- Key decisions and tradeoffs.
- Scope: domains, APIs, files, data, permissions, states.
- Evidence: changed files, tests, logs, commands, manual verification.
- Risks or follow-ups.

## Source Links (`--from-plan` / `--from-conversation`)

Pass the record the delivery came from so the task record links back to it. Three forms are accepted and all normalize to the same memory-root-relative path:

- bare record name — `2026-01-01_001_review-roles`
- memory-root relative — `conversation-records/2026-01-01_001_review-roles.md`
- project-root relative — `fengchao/conversation-records/2026-01-01_001_review-roles.md`

The CLI fills in the missing directory segment (`plan-records/` or `conversation-records/`) and the `.md` suffix. A value starting with `../` is treated as an explicit reference outside the memory root and is kept verbatim.

## Immutability

Do not rewrite old task records to update current truth. If a previous understanding becomes wrong, create a new task record and update `business-context/` to the latest truth with links to both records if useful.

## Index

`TASK-INDEX.md` must support quick lookup by:

- Recent task.
- Domain.
- Business topic or keyword.
- Risk/follow-up if notable.

The CLI writes a minimal recent-task table. Agents may add richer sections when useful.
