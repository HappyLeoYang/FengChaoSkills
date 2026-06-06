# Changelog System

`changelog/` records what changed in the delivered project. It is not a substitute for task records; it is the implementation history index.

## Entry Content

Each changelog entry should include:

- Change time.
- Domain.
- Change type.
- Link to the task record.
- Change summary.
- Business behavior change, if any.
- Implementation notes.
- Files touched.
- Verification performed.

## CHANGELOG-INDEX.md

This is the progressive entry point for history. It should help a future AI locate prior work without opening every changelog file.

Recommended sections:

- Recent changes.
- By domain.
- By API/entry point.
- By database/schema impact.
- By permissions/status/workflow changes.
- Historical traps or repeated issues.

The index should stay concise. Link out to individual entries for details.
