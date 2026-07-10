# Plan Records

`plan-records/` stores final plans from Plan mode or proposal work. A plan is not current business truth and must not update `business-context/` by default.

## Record Fields

- User goal.
- Current business understanding.
- Final plan.
- Assumptions.
- Open questions.
- Expected impact.
- Status: `proposed`, `approved`, `superseded`, `implemented`, or `abandoned`.
- Later links to task records and changelog when implemented.

## Capture Rule

Capture final plans only. Do not store every draft or back-and-forth.

## Status Backfill

When a plan lands (or is superseded/abandoned), update it with:

```bash
python3 .fengchao/skill/scripts/fengchao.py plan-status <plan-record-path> --status implemented --link <task-record-path>
```

This updates the record's status line, backfills the landing links, and syncs PLAN-INDEX and memory-map rows.
