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

## Record Fields

- Topic and domain.
- Extracted business background.
- Terms and meanings.
- Preferences and constraints.
- Rejected approaches.
- Unverified or not-yet-landed information.
- Related plan/task/changelog links.
- Promotion recommendation.
