---
name: Testing Conventions
description: "Use when writing or modifying tests under tests/. Covers the unit vs integration split, fixture patterns, and how to fake sessions and repositories."
applyTo: "tests/**/*.py"
---

# Testing Conventions

- `tests/unit/` — pure logic, no real DB or HTTP: monkeypatch repository methods directly (e.g.
  `monkeypatch.setattr(verify_email_service.token_repo, "get_active_by_hash_for_update", fake_fn)`)
  and use lightweight stand-ins (`types.SimpleNamespace` for entities, a hand-rolled `FakeSession`
  class implementing `begin()`/`__enter__`/`__exit__` for services that use
  `with session.begin():`).
- `tests/integration/` — exercise the real FastAPI app via `TestClient` against `app.main.app`,
  hitting actual routes under `/api/v1/...`.
- Mirror the source layout: `tests/unit/services/test_<service>.py`,
  `tests/integration/<feature>/test_<endpoint>.py`.
- Integration `client` fixture pattern: override `get_db` when the underlying service call is
  itself monkeypatched (`app.dependency_overrides[get_db] = lambda: object()`), yield a
  `TestClient(app)`, and always `app.dependency_overrides.clear()` in teardown.
- To intercept a service call in a router test, patch the name as imported into the API module,
  not the original service module: `monkeypatch.setattr(auth, "register_user", fake_register_user)`.
- `tests/conftest.py` sets `DATABASE_URL` from the `TEST_DATABASE_URL` env var for the whole
  session — don't touch a real dev/prod database from tests.
- Run the suite with `uv run pytest`.
