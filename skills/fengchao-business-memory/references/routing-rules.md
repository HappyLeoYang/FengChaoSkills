# Routing Rules

Use these rules after a completed development task to decide which memory files to update.

## Always Update (any delivery, lite or full)

- `changelog/YYYY-MM-DD_NNN_title.md`
- `changelog/CHANGELOG-INDEX.md`
- `memory-map.md`

## Additionally Update (full tier only — business meaning present)

- `task-records/YYYY-MM-DD_NNN_title.md`
- `task-records/TASK-INDEX.md`
- domain file rule entries via the `maintain` semantic merge (never by hand)

## Update business-context When Stable Business Truth Changed

Update domain context if the task changed:

- Business process, user workflow, state machine, approval flow, or permission rule.
- API contract, request/response semantics, validation, or error behavior.
- Data model semantics, persistence rules, identifier meaning, or cross-table copy behavior.
- Domain-specific calculation, default, fallback, or ordering rule.
- A historical trap, known limitation, or technical debt that future changes must consider.

## Do Not Update business-context For

- Pure formatting.
- Internal refactor with identical behavior.
- Test-only changes that do not document a business rule.
- Build tooling changes with no product behavior impact.
- Temporary debugging that did not land.

## Minimal Merge Rule

When context is needed, add the smallest durable fact:

- What is now true.
- Where it applies.
- What it depends on or affects.
- Link to the task record.

Avoid pasting implementation detail unless it is necessary to understand future business behavior.
