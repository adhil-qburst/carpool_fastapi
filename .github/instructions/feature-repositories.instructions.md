---
name: Feature Repositories
description: "Use when adding or modifying data-access classes in a feature's repositories/ folder. Keep repositories free of business logic and transaction control."
applyTo: "src/app/features/**/repositories/**/*.py"
---

# Feature Repositories

- One `XxxRepo` class per aggregate/model, plus a module-level factory `get_xxx_repo() -> XxxRepo`
  that returns a fresh, stateless instance (there is no DI container in this project).
- Every method takes `session: Session` as the first parameter, followed by keyword-only args for
  anything beyond a single id.
- Use `session.scalar(select(Model).where(...))` for single-row lookups, `session.get(Model, id)`
  for primary-key lookups, and `session.add(obj)` + `session.flush()` after creating a row so the
  generated id is available to the caller.
- Add `.with_for_update()` when a row must be locked for a subsequent update within the same
  transaction (see `get_active_by_hash_for_update` in
  [email_verification_tokens.py](../../src/app/features/users/repositories/email_verification_tokens.py)).
- Repositories must **not** call `session.commit()` or `session.rollback()` — transaction control
  belongs to the calling service.
- Repositories must **not** raise domain exceptions or perform validation — return `None`/the row
  and let `domain/rules.py` or the service decide what it means.
