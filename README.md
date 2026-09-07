project_name/
│
├── specs/
│   └── openapi.yaml                 # API contract / source specification
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_create_users.py
│       ├── 002_create_locations.py
│       └── ...
│
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── core/                    # Application-wide infrastructure
│       │   ├── __init__.py
│       │   ├── config.py            # Environment / settings
│       │   ├── security.py          # JWT, password hashing
│       │   └── exceptions.py
│       │
│       ├── db/                      # Database infrastructure
│       │   ├── __init__.py
│       │   ├── base.py              # SQLAlchemy Base
│       │   └── session.py            # DB session
│       │
│       ├── domain/                  # Business/domain layer
│       │   ├── __init__.py
│       │   │
│       │   ├── common/
│       │   │   ├── __init__.py
│       │   │   └── enums.py          # Shared enums
│       │   │
│       │   ├── users/
│       │   │   ├── __init__.py
│       │   │   ├── enums.py          # UserRole
│       │   │   ├── entities.py       # User domain entity
│       │   │   └── rules.py          # User business rules
│       │   │
│       │   ├── locations/
│       │   │   ├── entities.py
│       │   │   └── rules.py
│       │   │
│       │   ├── routes/
│       │   │   ├── entities.py
│       │   │   └── rules.py
│       │   │
│       │   ├── trips/
│       │   │   ├── entities.py
│       │   │   └── rules.py
│       │   │
│       │   ├── bookings/
│       │   │   ├── entities.py
│       │   │   └── rules.py
│       │   │
│       │   ├── vehicles/
│       │   │   ├── entities.py
│       │   │   └── rules.py
│       │   │
│       │   └── reviews/
│       │       ├── entities.py
│       │       └── rules.py
│       │
│       ├── models/                  # SQLAlchemy persistence models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── location.py
│       │   ├── route.py
│       │   ├── route_stop.py
│       │   ├── trip.py
│       │   ├── booking.py
│       │   ├── vehicle.py
│       │   └── review.py
│       │
│       ├── schemas/                 # Pydantic API contracts
│       │   ├── __init__.py
│       │   ├── auth/
│       │   │   ├── register.py
│       │   │   ├── login.py
│       │   │   └── token.py
│       │   ├── users/
│       │   │   ├── create.py
│       │   │   ├── update.py
│       │   │   └── response.py
│       │   ├── locations/
│       │   ├── routes/
│       │   ├── trips/
│       │   ├── bookings/
│       │   ├── vehicles/
│       │   └── reviews/
│       │
│       ├── api/                     # HTTP layer
│       │   ├── __init__.py
│       │   ├── router.py
│       │   ├── auth.py
│       │   ├── locations.py
│       │   ├── routes.py
│       │   ├── trips.py
│       │   ├── bookings.py
│       │   ├── vehicles.py
│       │   └── reviews.py
│       │
│       ├── services/                # Application/use-case layer
│       │   ├── auth/
│       │   │   ├── register.py
│       │   │   ├── login.py
│       │   │   └── refresh.py
│       │   ├── routes/
│       │   ├── trips/
│       │   ├── bookings/
│       │   ├── vehicles/
│       │   └── reviews/
│       │
│       └── repositories/            # Database access
│           ├── users.py
│           ├── locations.py
│           ├── routes.py
│           ├── trips.py
│           ├── bookings.py
│           ├── vehicles.py
│           └── reviews.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── services/
│   │
│   ├── integration/
│   │   ├── repositories/
│   │   └── db/
│   │
│   └── contract/
│       └── openapi/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md