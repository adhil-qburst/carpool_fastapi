---
name: Feature API Routers
description: "Use when adding or modifying FastAPI route handlers under a feature's api/ folder. Keep routers thin and translate domain exceptions to HTTP responses consistently."
applyTo: "src/app/features/**/api/**/*.py"
---

# Feature API Routers

- Create one `router = APIRouter()` per feature file; wire it into
  [src/app/api/router.py](../../src/app/api/router.py) with `api_router.include_router(router, prefix="/<feature>", tags=["<Feature>"])`.
- Handlers must stay thin: accept a `schemas/` request model, call exactly one `services/`
  function, and return a `schemas/` response model. No business logic or DB queries in the router.
- Depend on a DB session with `db: Session = Depends(get_db)` from `app.db.session`.
- Catch each feature exception explicitly and re-raise as `HTTPException`, preserving the chained
  cause:

  ```python
  except SomeFeatureError as exc:
      raise HTTPException(status_code=status.HTTP_4xx, detail=exc.detail) from exc
  ```

- Pick the status code per error meaning (already-exists → 409, invalid input the domain rejected
  → 400, external dependency failure like email delivery → 503, not found → 404). Never leak a raw
  `AppError` past the router.
- Use `status.HTTP_*` constants from `fastapi`, not bare integers, and set `status_code=` /
  `response_model=` on the decorator when the success response isn't a plain 200.
- Import the service function directly (`from app.features.<feature>.services.<name> import
  <fn>`) so tests can `monkeypatch.setattr(<api_module>, "<fn>", fake)` on the router module.
