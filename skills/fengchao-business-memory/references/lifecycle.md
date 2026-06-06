# Lifecycle

## Mode Decision

Choose one mode per situation:

- **FengWang routing**: a new user request arrives in a project that has FengChao memory.
- **Plan capture**: Plan mode or proposal work produced a final plan.
- **Conversation capture**: the user explained durable business context, terminology, preferences, constraints, or rejected options.
- **Development completion**: a real development task produced delivered project changes.

Only development completion writes `task-records/` and `changelog/`.

## Non-Development Modes

- Plan capture writes `plan-records/` and updates `fengwang/memory-map.md`.
- Conversation capture writes `conversation-records/` and updates `fengwang/memory-map.md`.
- Neither mode writes `business-context/` unless the user explicitly confirms the information is current business truth.

## Development Completion Flow

1. Gather evidence from the current conversation, final implementation, changed files, and verification output.
2. Write one immutable `task-records/YYYY-MM-DD_NNN_title.md`.
3. Write one `changelog/YYYY-MM-DD_NNN_title.md`.
4. Update `TASK-INDEX.md` and `CHANGELOG-INDEX.md`.
5. Merge only stable landed business facts into `business-context/`.
6. Update `fengwang/memory-map.md`.
7. Run `fengchao check`.
8. In the final response, mention the memory artifacts updated and any verification gap.

## Source Priority

1. Final conversation outcome and user-confirmed intent.
2. Implemented code and tests.
3. Git diff and file list.
4. Existing business context and historical records.

Diff is evidence, not the memory source. The business memory should explain why the change exists and what business fact is now true.

## Privacy Default

Store only extracted summaries. Do not archive complete conversations by default. Include short user wording only when it is necessary to preserve a business term or rule.
