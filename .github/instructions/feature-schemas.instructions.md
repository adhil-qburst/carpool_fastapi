---
name: Feature Schemas
description: "Use when adding or modifying Pydantic request/response models in a feature's schemas/ folder. Covers naming, normalization validators, and reuse of domain enums."
applyTo: "src/app/features/**/schemas/**/*.py"
---

# Feature Schemas

- One file per action (`register.py`, `login.py`, ...), containing a `<Action>Request` and/or
  `<Action>Response` `pydantic.BaseModel`. Keep response-only files to a single `<Action>Response`.
- Normalize user input at the schema boundary with `@field_validator`, not in services — e.g. trim
  and lowercase emails, reject blank strings after stripping. Return the normalized value from the
  validator.
- Reuse `domain/enums.py` types for constrained fields (e.g. `roles: list[UserRole]`) instead of
  raw `str`, so FastAPI validates allowed values and returns `422` automatically.
- Use `Field(..., min_length=..., max_length=...)` for size constraints instead of custom
  validators when a simple constraint suffices.
- Response models should mirror exactly what the router returns — don't add fields the service
  doesn't populate.
