---
name: Feature Domain Layer
description: "Use when adding or modifying enums, invariant rules, or non-persisted entities in a feature's domain/ folder."
applyTo: "src/app/features/**/domain/**/*.py"
---

# Feature Domain Layer

- `enums.py`: define status/role/type fields as `class Foo(StrEnum)`. Pair every domain enum used
  in a model column with `SQLEnum(Foo, name="foo", values_callable=lambda enum: [m.value for m in
  enum])` in the corresponding `models/` file so the DB stores the string value, not the member
  name.
- `rules.py`: small, pure functions named `ensure_*` (guard clauses) or plain verbs (`normalize_*`)
  that take already-fetched entities/values and either return a normalized value or raise the
  feature's `AppError` subclass from `exceptions.py`. Rules must not query the database or accept a
  `Session` — fetch data in the repository/service first, then pass it in.
- `entities/`: plain `pydantic.BaseModel` value objects for data that crosses layers but isn't
  persisted (e.g. `AuthToken`). Do not use these for anything that has a `models/` table — that
  belongs in a SQLAlchemy model instead.
