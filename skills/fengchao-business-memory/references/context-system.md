# Progressive Business Context

`business-context/` is the current business truth of the project. It is mutable and optimized for a fresh AI conversation to regain context quickly.

## Required Structure

```text
business-context/
  CONTEXT-INDEX.md
  domains/
  project-facts.md
  impact-matrix.md
  debt-registry.md
```

Optional subdirectories (`architecture/`, `data/`) may be added when the project needs them.

## Rule Entries (domain files)

Each domain file keeps two managed sections: `## 当前业务规则` (current rules) and `## 已废除规则` (retired rules). A current rule is a structured entry keyed by a stable rule name:

```markdown
### 规则：设计单审核流程
- **规则**：设计单最终通过必须依次经过主管审核和经理审核。
- **场景**：设计师提交后，主管一审通过、经理二审通过才进入"已通过"状态；任一级驳回整单退回。
- **来源**：[task-record 链接]
- **生效**：YYYY-MM-DD
- **沿革**：[历任旧版本 task-record 链接，最近的在前]
```

Never edit these sections by hand: they are maintained exclusively by `maintain --business-change --change-kind added|modified|removed --rule-name ...` so that one rule name always has exactly one active entry. Terms, preferences, pitfalls, and rejected options do NOT use this format — they live in conversation-records and the debt registry.

## project-facts.md

Registers discrete project facts the user asserted with certainty in conversation: entry points, config
values, term anchors, code conventions. It answers "what is X in this project" — **not** "what rule governs
X", which belongs in a domain file.

```markdown
### 事实：设计单提交审核入口
- **类别**：entry-point
- **事实**：POST /liangang/workorder/submitReview
- **来源**：[对话记录链接]
- **更新**：YYYY-MM-DD
- **沿革**：[历任旧来源链接，最近的在前]
```

Same discipline as domain rules: the fact name is a stable key, at most one active entry per name, and the
section is maintained exclusively by `conversation --confirmed-fact` / `--retire-fact`. Never edit by hand.

Two limits worth stating plainly:

- **Facts are clues, not guarantees.** `check` does not verify them against source code — the CLI is
  dependency-free and language-agnostic by design. When a registered fact contradicts the code, the code
  wins; tell the user the registration is stale.
- **Scope stops at the mapping.** Register "business name ↔ where it lives". Do not record parameters,
  field lists, or return shapes — that is a second-rate copy of API docs and will rot faster than it helps.

## CONTEXT-INDEX.md

Must answer:

- What the project does in one paragraph.
- The main business chain or workflow.
- Which documents to read first for common request types.
- Key IDs, entities, states, permissions, or contracts that connect domains.
- Links to task and changelog indexes for historical traceability.

## Domain Documents

Each `domains/domain-*.md` should contain:

- Domain purpose.
- Current business rules.
- Core entry points: UI screens, APIs, services, jobs, tables, or config.
- Upstream and downstream dependencies.
- Known risks or historical traps.
- Links to relevant task records or changelog entries.

## Update Policy

Update context only with stable facts that landed in the project. Do not copy a whole changelog entry into a domain file. Add the smallest business fact that helps a future AI avoid re-asking the user.

If a task is purely technical and does not change business behavior, do not force a business-context update.
