# CarPool Server — Project Guidelines

FastAPI + SQLAlchemy 2 + PostgreSQL backend for a route-based carpooling platform. See
[docs/carpool-project-plan.md](../docs/carpool-project-plan.md) for the domain model and roadmap.

## Architecture

Feature-based (vertical slice) layout under `src/app/features/<feature>/`. Each feature owns its
own slice through these layers, called in this order:

```
api/ (FastAPI router)  →  services/ (business logic)  →  repositories/ (SQLAlchemy queries)  →  models/ (ORM tables)
                                   ↑ uses
                             domain/ (enums, invariant rules, non-persisted entities)
                                   ↓ raises
                             exceptions.py (feature-specific AppError subclasses)
```

- `api/` — thin route handlers: validate via a `schemas/` Pydantic model, call a service function,
  catch that feature's `AppError` subclasses and translate to `HTTPException(detail=exc.detail)`.
- `services/` — plain functions (not classes) that own the DB transaction (`session.commit()` /
  `session.rollback()`, or `with session.begin():`) and raise domain exceptions on failure.
- `repositories/` — one `XxxRepo` class per aggregate + a `get_xxx_repo()` factory. Pure data
  access only; never commits/rolls back.
- `domain/` — `enums.py` (StrEnum), `rules.py` (pure invariant checks that raise exceptions),
  `entities/` (non-persisted Pydantic DTOs).
- Cross-cutting code lives in `src/app/core/` (config, security, email, base `AppError`) and
  `src/app/db/` (SQLAlchemy `Base`, engine/session factory, `get_db` FastAPI dependency).
- Background jobs use Dramatiq + RabbitMQ (`src/app/tasks/`); actors are registered on a shared
  broker and enqueued from services with `.send(...)`.
- Routers are aggregated in [src/app/api/router.py](../src/app/api/router.py) under `/api/v1`.

Layer-specific conventions are captured in `.github/instructions/*.instructions.md` and are
auto-attached when you edit matching files — read them before adding code to that layer. For
scaffolding an entirely new feature module, see the
[new-feature-module skill](./skills/new-feature-module/SKILL.md).

## Build and Test

This project is managed with `uv` (see `uv.lock`).

```bash
uv sync                                          # install dependencies
uv run uvicorn app.main:app --app-dir src --reload   # run the API locally
uv run pytest                                    # run tests
uv run alembic upgrade head                      # apply migrations
uv run dramatiq app.tasks.worker                 # run the background worker
```

## Conventions

- Python 3.14+, SQLAlchemy 2 typed `Mapped`/`mapped_column` models, UUID primary keys.
- Errors flow as exceptions, not return codes: raise a feature `AppError` subclass deep in the
  stack, only convert to `HTTPException` at the API layer.
- Never hand-write files under `alembic/versions/`; generate migrations with
  `alembic revision --autogenerate` and apply with `alembic upgrade head`.
- Keep `openapi.yaml` in sync when adding or changing endpoints (this project is spec-first).
