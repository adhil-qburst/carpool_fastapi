---
name: Feature Services
description: "Use when adding or modifying business logic in a feature's services/ folder. Covers transaction ownership, settings injection, repository usage, and exception raising."
applyTo: "src/app/features/**/services/**/*.py"
---

# Feature Services

- Write plain module-level functions, not classes. First positional parameter is the SQLAlchemy
  `session: Session`; accept a `schemas/` request object or explicit kwargs after it.
- Accept an optional `settings: Settings | None = None` keyword-only parameter and resolve it with
  `settings = settings or get_settings()` — never call `get_settings()` unconditionally so callers
  and tests can inject fakes.
- Obtain repositories via their `get_xxx_repo()` factory functions inside the service; don't
  instantiate `XxxRepo()` directly or accept them as parameters.
- Enforce invariants by calling `domain/rules.py` helpers (e.g. `ensure_email_is_available`) rather
  than inlining `if` checks — the rule functions raise the feature's `AppError` subclasses.
- The service owns the transaction boundary:
  - For a single atomic block, prefer `with session.begin(): ...` (see
    [verify_email.py](../../src/app/features/auth/services/verify_email.py)).
  - Otherwise, call `session.commit()` on the success path and `session.rollback()` in `except`
    blocks before re-raising (see [login.py](../../src/app/features/auth/services/login.py)).
- Never raise `HTTPException` here — only raise feature `AppError` subclasses; the API layer is
  responsible for the HTTP translation.
- If a service enqueues background work, do it through the relevant `tasks/*.send(...)` actor, not
  by importing task internals directly.
