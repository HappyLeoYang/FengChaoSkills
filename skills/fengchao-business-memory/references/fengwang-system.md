# FengWang System

FengWang is the project memory router. A fresh AI conversation should start from `<memory-root>/FENGWANG.md` (default `fengchao/FENGWANG.md`; legacy layout `fengwang/FENGWANG.md`), then use `memory-map.md` or `fengchao.py fengwang --query` to find the smallest relevant memory set.

Routing output is byte-budgeted (default 4KB). Read the top 3 results first; if the output says it was truncated, refine the query instead of loading more.

## Responsibilities

- Route a user request to current context, conversation memories, plans, tasks, and changelog entries.
- Prevent full-history loading.
- Preserve memory semantics: current fact, implemented task, historical change, proposed plan, or conversation context.

## Query Flow

1. Extract terms from the user request: domain, workflow, role, state, API, file, page, table, or keyword.
2. Match against `memory-map.md`.
3. Read current facts first.
4. Read historical/contextual records only when they directly help the request.

Conflict priority:

`business-context` > `task-records/changelog` > `implemented plan` > `conversation-records` > `proposed plan`.
