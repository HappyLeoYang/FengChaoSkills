# Progressive Business Context

`business-context/` is the current business truth of the project. It is mutable and optimized for a fresh AI conversation to regain context quickly.

## Required Structure

```text
business-context/
  CONTEXT-INDEX.md
  domains/
  architecture/
  data/
  impact-matrix.md
  debt-registry.md
```

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
