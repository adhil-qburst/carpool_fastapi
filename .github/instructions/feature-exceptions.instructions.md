---
name: Feature Exceptions
description: "Use when adding or modifying a feature's exceptions.py. Covers the AppError subclassing pattern and where these exceptions may be caught."
applyTo: "src/app/features/**/exceptions.py"
---

# Feature Exceptions

- Every feature has its own `exceptions.py`; each error is a class that subclasses
  `app.core.exceptions.AppError`.
- `AppError.__init__(self, detail: str, code: str | None = None)` — always pass a user-facing
  `detail` message and an `UPPER_SNAKE_CASE` machine-readable `code`:

  ```python
  class EmailAlreadyRegisteredError(AppError):
      def __init__(self, user: User) -> None:
          self.user = user  # extra context the caller may need to recover
          super().__init__("An account with this email already exists.", "EMAIL_ALREADY_REGISTERED")
  ```

- Store any extra context the catching layer needs (e.g. the conflicting `User`, an `email`/
  `user_id` pair) as attributes set *before* calling `super().__init__(...)`.
- These exceptions should only ever be caught in two places: the feature's own `services/` layer
  (to react and re-raise, e.g. sending a token then re-raising `UnVerifiedUserError`) or the
  `api/` router layer (to translate to `HTTPException`). Repositories and domain rule functions
  raise them but never catch them.
- Double-check `super().__init__(...)` is spelled with two leading and two trailing underscores —
  a single typo here (`_init__`) silently breaks the exception's constructor.
