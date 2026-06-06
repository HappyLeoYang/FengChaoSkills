# Memory Promotion Rules

FengChao keeps memory layers separate so future AI sessions do not confuse proposals with current truth.

## Promotion To business-context

Promote only when:

- A development task implemented the fact.
- The user explicitly confirms it as current business truth.
- Existing code or authoritative project docs verify it.

## Do Not Promote

- Proposed plans.
- Unverified conversation explanations.
- Rejected approaches.
- Historical behavior that has since changed.

## Conflict Priority

1. `business-context/` current facts.
2. `task-records/` and `changelog/` implemented evidence.
3. Implemented `plan-records/`.
4. `conversation-records/`.
5. Proposed or abandoned `plan-records/`.
