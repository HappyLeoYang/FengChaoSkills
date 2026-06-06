# FengWang System

FengWang is the project memory router. A fresh AI conversation should start from `fengwang/FENGWANG.md`, then use `fengwang/memory-map.md` or `fengchao.py fengwang --query` to find the smallest relevant memory set.

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
