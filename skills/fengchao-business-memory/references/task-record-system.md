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

## Immutability

Do not rewrite old task records to update current truth. If a previous understanding becomes wrong, create a new task record and update `business-context/` to the latest truth with links to both records if useful.

## Index

`TASK-INDEX.md` must support quick lookup by:

- Recent task.
- Domain.
- Business topic or keyword.
- Risk/follow-up if notable.

The CLI writes a minimal recent-task table. Agents may add richer sections when useful.
