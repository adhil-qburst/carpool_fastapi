# Carpool Server

```text
carpool_server/
├── alembic/                         # Database migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0c55d737e91a_email_verification_table.py
│       └── 4d03402f54f9_add_the_user_table.py
├── docs/
│   └── carpool-project-plan.md
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py                  # FastAPI application entry point
│       ├── api/                     # HTTP routes and router registration
│       │   ├── __init__.py
│       │   └── router.py
│       ├── core/                    # Application-wide configuration and utilities
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── email.py
│       │   ├── exceptions.py
│       │   └── security.py
│       ├── db/                      # Database setup and SQLAlchemy base
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── session.py
│       └── features/                # Feature-oriented application modules
│           ├── __init__.py
│           ├── auth/
│           │   ├── __init__.py
│           │   ├── api/
│           │   │   └── auth.py
│           │   └── schemas/
│           │       ├── register.py
│           │       └── verify_email.py
│           └── users/
│               ├── __init__.py
│               ├── domain/
│               │   ├── enums.py
│               │   └── rules.py
│               ├── models/
│               │   ├── email_verification_token.py
│               │   └── user.py
│               ├── repositories/
│               │   ├── email_verification_tokens.py
│               │   └── users.py
│               └── services/
│                   ├── register.py
│                   └── verify_email.py
├── tests/
│   ├── conftest.py
│   └── integration/
│       └── auth/
│           └── test_register_user.py
├── alembic.ini
├── openapi.yaml                     # API contract
├── pyproject.toml
├── uv.lock
└── README.md
```
