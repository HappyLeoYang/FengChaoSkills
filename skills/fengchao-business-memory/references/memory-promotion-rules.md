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

## Two Promotion Channels

The three conditions above map to two write channels — there is no hand-editing path:

| Condition | Channel | Lands in |
|-----------|---------|----------|
| A development task implemented the fact | `maintain --business-change` | `domains/domain-*.md` |
| The user explicitly confirms it as current truth | `conversation --confirmed-fact` | `project-facts.md` |
| Existing code verifies it | **neither** — see below | — |

The third condition is the trap. Code confirms what the code *does*, not what the business *means*: a
check in a service method may be a deliberate rule, a defensive leftover, or a bug. What the AI reads out
of source code is a **candidate**, not a fact. Record it as unverified (or `--promote candidate`) and ask
the user; register it only after they confirm. Skipping that step is how a business-memory system decays
into a summary of whatever the code happens to say today.

## Conflict Priority

1. `business-context/` current facts (domain rules and `project-facts.md`).
2. `task-records/` and `changelog/` implemented evidence.
3. Implemented `plan-records/`.
4. `conversation-records/`.
5. Proposed or abandoned `plan-records/`.

When a registered fact and the current code disagree, the code wins for the immediate answer — but say so
explicitly and offer to re-register the fact. Nothing revalidates `project-facts.md` automatically.
