# Conversation Records

`conversation-records/` stores durable context extracted from user conversation. It is contextual memory, not current business truth by default.

## Capture When

- The user explains business background that future AI sessions should remember.
- The user defines terms, roles, statuses, or workflow boundaries.
- The user states durable preferences or constraints.
- The user rejects an approach and the rejection should be respected later.

## Do Not Capture

- Short-lived clarifications.
- Sensitive raw conversation.
- Every ordinary message.
- Speculation not useful for future tasks.

## Confirmed Facts (`--confirmed-fact`)

A conversation record is contextual memory, but a fact the user **asserts with certainty** during that
conversation is current truth and is registered into `business-context/project-facts.md` in the same call.

- Gate: `references/extraction-quality.md` section 5 (certainty-signal checklist). **Strict by default —
  prefer missing a fact over registering a wrong one.**
- Only four kinds of statement qualify: an affirmative statement about the project's current state; a
  correction of the AI's wrong belief; an answer to a factual question the AI asked; an explicit
  "remember this".
- Never register: questions, hedged wording ("probably", "I think"), undecided options, or anything the
  AI inferred from source code (that goes to "Unverified" or `--promote candidate` until the user confirms).
- Fact types are open: entry points, config values, term anchors, code conventions, IDs, states.
- The fact name is a stable key. Same name registered again overwrites the value and moves the old source
  into history. Use `--retire-fact` only when the fact itself is void, not when its value merely changed.
- Ask before writing, in a single line at the end of the current reply — do not interrupt the conversation.

## Record Fields

- Topic and domain.
- Extracted business background.
- Terms and meanings.
- Preferences and constraints.
- Rejected approaches.
- Unverified or not-yet-landed information.
- Related plan/task/changelog links.
- Promotion recommendation.
