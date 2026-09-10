---
name: SQLAlchemy Model Generation
description: "Use when creating or modifying SQLAlchemy models in src/app/features/*/models. Preserve the project's model conventions, never create migration scripts for model generation, and show commands for generating and applying migrations."
applyTo: "src/app/features/**/models/**/*.py"
---

# SQLAlchemy Model Generation

- Use SQLAlchemy 2 typed mappings with `Mapped` and `mapped_column` based on the existing models.
- Use PostgreSQL UUID primary keys with `uuid.uuid4` defaults unless the task explicitly requires another type.
- Include timezone-aware `created_at` and `updated_at` columns when adding a persistent model, using the existing `server_default=func.now()` and `onupdate=func.now()` pattern.
- Define foreign keys and relationships consistently with the existing models, including `ondelete="CASCADE"` where ownership requires it.
- Keep model generation separate from migration generation. Never create, modify, or delete files under `alembic/versions/`, and do not run `alembic revision --autogenerate` for a model-generation request.
- When reporting model changes, show the command the user can run to create the migration script, replacing `<ModelName>` with the model name:

  ```bash
  alembic revision --autogenerate -m "create <ModelName> model"
  ```

- Also show the command to apply existing migration scripts:

  ```bash
  alembic upgrade head
  ```

- Link to [the project plan](../../docs/carpool-project-plan.md) when broader domain-model context is relevant instead of duplicating its contents.