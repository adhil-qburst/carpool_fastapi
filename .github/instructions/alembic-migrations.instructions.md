---
name: Alembic Migrations
description: "Use when creating, editing, or reviewing Alembic migration scripts under alembic/versions, including schema migrations and data-seed migrations."
applyTo: "alembic/versions/**/*.py"
---

# Alembic Migrations

- Generate schema migrations from models, don't hand-write them:
  `uv run alembic revision --autogenerate -m "<message>"`, then apply with
  `uv run alembic upgrade head`.
- Keep the generated header docstring (summary, `Revision ID`, `Revises`, `Create Date`) and the
  `revision` / `down_revision` / `branch_labels` / `depends_on` variables typed as
  `Union[str, Sequence[str], None]` exactly as Alembic templates them.
- For **data seed migrations** (not schema changes), follow
  [b7c4d9e2f1a0_seed_location_data.py](../../alembic/versions/b7c4d9e2f1a0_seed_location_data.py):
  - Read seed rows from a JSON file under `src/seeds/data/` via `Path(__file__).resolve().parents[2]`.
  - Derive deterministic primary keys with `uuid.uuid5(uuid.NAMESPACE_URL, f"<stable-key>")` so
    `upgrade()` is idempotent and `downgrade()` can precisely target the same rows.
  - Insert with `sa.table(...)` + `op.bulk_insert(...)`, never raw hardcoded row literals.
  - Always implement `downgrade()` to delete exactly the rows `upgrade()` inserted (recompute the
    same ids, then `DELETE ... WHERE id IN (...)`).
- Never edit a migration file that has already been applied anywhere outside local dev; create a
  new migration instead.
- Don't mix a schema change and a data seed in the same revision — keep them as separate,
  sequential migrations.
