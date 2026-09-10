---
name: new-feature-module
description: 'Use when adding a brand-new feature module (e.g. vehicles, routes, trips, bookings, reviews) to the CarPool FastAPI backend. Scaffolds the full vertical slice — domain enums/rules, SQLAlchemy models, repositories, services, schemas, exceptions, and API router wiring — following the existing auth/users/location conventions, and generates the matching migration.'
---

# New Feature Module

Scaffold a new `src/app/features/<feature>/` vertical slice. Follow this order; each layer's
detailed conventions are in the linked instructions file.

## 1. Package layout

Create `src/app/features/<feature>/` with `__init__.py`, an `exceptions.py`, and subfolders
`domain/`, `models/`, `repositories/`, `services/`, `schemas/`, `api/` (only add the subfolders the
feature actually needs — not every feature has all of them, e.g. `location` has no `services/`).

## 2. Domain layer

See [feature-domain.instructions.md](../../instructions/feature-domain.instructions.md).
Add `domain/enums.py` for any status/role/type field, `domain/rules.py` for invariant checks, and
`domain/entities/` for any non-persisted cross-layer DTO.

## 3. Exceptions

See [feature-exceptions.instructions.md](../../instructions/feature-exceptions.instructions.md).
Define one `AppError` subclass per expected failure mode before writing the services that raise
them.

## 4. Models

See [sqlalchemy-model-generation.instructions.md](../../instructions/sqlalchemy-model-generation.instructions.md).
Do **not** create or edit anything under `alembic/versions/` yet.

## 5. Repositories

See [feature-repositories.instructions.md](../../instructions/feature-repositories.instructions.md).
One `XxxRepo` class + `get_xxx_repo()` factory per model.

## 6. Services

See [feature-services.instructions.md](../../instructions/feature-services.instructions.md).
Plain functions that take the session, use the repos/domain rules, own the transaction, and raise
the feature's exceptions.

## 7. Schemas

See [feature-schemas.instructions.md](../../instructions/feature-schemas.instructions.md).
`<Action>Request` / `<Action>Response` Pydantic models per action.

## 8. API router

See [feature-api-routers.instructions.md](../../instructions/feature-api-routers.instructions.md).
Create `api/<feature>.py` with `router = APIRouter()`, then wire it into
[src/app/api/router.py](../../../src/app/api/router.py):

```python
from app.features.<feature>.api import <feature>
api_router.include_router(<feature>.router, prefix="/<feature>", tags=["<Feature>"])
```

## 9. Migration

Once the models are final, generate and report (don't run silently) the migration commands:

```bash
uv run alembic revision --autogenerate -m "create <feature> tables"
uv run alembic upgrade head
```

See [alembic-migrations.instructions.md](../../instructions/alembic-migrations.instructions.md) if
the feature also needs seed data.

## 10. Tests

See [testing-conventions.instructions.md](../../instructions/testing-conventions.instructions.md).
Add `tests/unit/services/test_<service>.py` for business logic and
`tests/integration/<feature>/test_<endpoint>.py` for the HTTP contract.

## 11. Spec

This project is spec-first — update [openapi.yaml](../../../openapi.yaml) with the new endpoints'
request/response schemas alongside the implementation.
