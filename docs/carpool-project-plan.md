# Project Plan: CarPool — A Route-Based Carpooling Platform

This plan replaces the generic tech-stack exercise with a single concrete product: **CarPool**, a ride-sharing platform where drivers register fixed routes (source → intermediate stops → destination) and riders search for a matching route with available seats. You'll build it in three architectural stages, in this order:

1. **Local** — FastAPI + SQLAlchemy + PostgreSQL + Celery + Redis + React, all running on your machine.
2. **Dockerized** — the exact same architecture, containerized (no redesign, just packaging).
3. **Cloud-native, event-driven** — API on Lambda behind API Gateway, background jobs as independent Lambda functions, SQS replacing Redis/Celery as the broker, frontend on S3 + CloudFront, media on S3.

The architecture is designed so Stage 3 is a **re-platforming of the same domain logic**, not a rewrite — the business logic (matching algorithm, booking rules) barely changes; only *how it's invoked* changes.

---

## 0. Domain Model (design this before any code)

This is the backbone everything else hangs off. Get it right first.

| Entity | Key fields | Notes |
|---|---|---|
| `User` | id, name, email, password_hash, role(s) | A user can be a driver, rider, or both — don't hardcode a single role. |
| `Vehicle` | id, driver_id, make, model, plate, seat_count, photo_url | Belongs to a driver. |
| `Location` | id, name, city, lat, lng | Seeded via data migration — see §2. |
| `Route` | id, driver_id, vehicle_id, name | A **template**: "Route A" from City X to City Y. |
| `RouteStop` | id, route_id, location_id, sequence, eta_offset_minutes | Ordered stops on a route. `sequence` is the ordering key your matching algorithm depends on. |
| `Trip` | id, route_id, departure_date, departure_time, available_seats, status | An actual **scheduled instance** of a route. Routes are reusable templates; trips are bookable occurrences. |
| `Booking` | id, trip_id, rider_id, pickup_stop_id, dropoff_stop_id, seats_booked, status | Status: `PENDING`, `CONFIRMED`, `CANCELLED`, `EXPIRED`. |
| `Review` | id, booking_id, rating, comment | Optional but good for "basic API development" breadth. |

**Why Route vs. Trip matters:** if you skip this distinction, you'll conflate "a route that exists" with "a seat available on a specific date," and seat-availability logic gets tangled with route-matching logic. Keep them separate from day one.

---

## 1. Spec-Driven Development: Design the Contract First

**Do:**
- Write `openapi.yaml` covering all endpoints below before implementing any of them. Include request/response schemas for every entity in §0.
- Core endpoints to spec:
  - `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
  - `GET /locations?search=` (autocomplete for source/destination pickers)
  - `POST /routes` (driver creates a route with ordered stops), `GET /routes/{id}`
  - `POST /trips` (driver schedules a route instance), `GET /trips?route_id=`
  - `POST /search` (rider searches: `source_location_id`, `destination_location_id`, `date`, `seats_needed` → returns matching trips)
  - `POST /bookings`, `GET /bookings/{id}`, `PATCH /bookings/{id}/cancel`
  - `POST /vehicles`, `POST /vehicles/{id}/photo` (media upload)
  - `POST /reviews`
  - `GET /health`, `GET /ready`
- Validate the spec with `openapi-spec-validator`.

**Checkpoint:** A reviewed, valid spec that a frontend developer could build against without ever seeing your backend code.

---

## 2. Data Migration & Seeding — Locations and Route Graph

This is the part you specifically flagged, so treat it as its own milestone, not a throwaway script.

**Learn:**
- Alembic **data migrations** (not just schema migrations) — a migration that inserts rows, not just creates tables.
- Idempotent seeding patterns (`INSERT ... ON CONFLICT DO NOTHING`) so re-running a migration doesn't duplicate data.

**Do:**
- Write an Alembic migration that seeds `locations` with a fixed set of cities/stops (e.g., 15–20 locations forming a small transit-like network).
- Write a second migration seeding `routes` + `route_stops` — a handful of routes, each an ordered path through 3–6 locations, designed so some routes **overlap** (shared intermediate stops) to make matching interesting.
- Model this conceptually as a **directed graph**: locations are nodes, each route is a path. Draw it on paper or in a diagram tool before writing the migration — it's much easier to write correct `sequence` values from a picture.
- Keep the seed data in a structured file (`seed_data/locations.json`, `seed_data/routes.json`) that the migration reads, rather than hardcoding rows inline — this makes it easy to regenerate or extend later.

**Checkpoint:** `alembic upgrade head` on a blank database produces a fully populated, internally consistent route network — no manual SQL needed.

---

## 3. Core Matching Algorithm (the interesting part)

**Learn:**
- Basic graph/path concepts: given a rider's source and destination, find trips whose route contains **both** stops, in the correct order (source's `sequence` < destination's `sequence`).
- Why this is *not* a shortest-path problem (you're not routing between arbitrary points — you're filtering existing fixed routes), which keeps the first version simpler than it sounds.

**Do:**
- Implement `find_matching_trips(source_location_id, destination_location_id, date, seats_needed)`:
  1. Find all `RouteStop` rows matching `source_location_id` and `destination_location_id`.
  2. Filter to routes where both appear with `source.sequence < destination.sequence`.
  3. Join to `Trip` for the given date with `available_seats >= seats_needed` and `status = SCHEDULED`.
  4. Return trips with driver, vehicle, ETA between the two stops (`eta_offset_minutes` difference).
- Write this as a plain, well-tested Python function *before* wiring it to an endpoint — it's the piece most worth unit-testing thoroughly.
- Stretch goal: partial-route stitching (rider's journey requires *two* connecting trips because no single route covers it) — mark this as a v2 feature, not part of the MVP, so scope doesn't balloon.

**Checkpoint:** Given your seeded route graph, a rider searching two overlapping-route cities gets correct multi-driver results; searching two disconnected cities returns an empty, correctly-explained result.

---

## 4. FastAPI Backend — Core API

**Do (building on the earlier general-stack plan's FastAPI/SQLAlchemy/Postgres phases):**
- Implement all endpoints from the spec in §1 against the real schema.
- **Auth:** JWT-based, with `Depends()`-based current-user extraction and role checks (driver-only endpoints like `POST /routes` vs. rider-only like `POST /bookings`).
- **Pagination & filtering:** `GET /trips` should support `?page=&limit=` and filters (date range, min seats).
- **Rate limiting:** add basic middleware (e.g., `slowapi`) on the search endpoint, since it's your most expensive read.
- **Media upload:** `POST /vehicles/{id}/photo` — for now, store to local disk or **MinIO** (an S3-compatible local server) rather than the actual filesystem, since MinIO's API is what you'll swap directly for real S3 later with almost no code changes (this is the single most valuable shortcut in this whole plan — use it).
- **Seat concurrency:** two riders booking the last seat simultaneously is a real race condition — handle it with a `SELECT ... FOR UPDATE` row lock or an optimistic-concurrency version column on `Trip`. This is worth deliberately testing (see §6).

**Checkpoint:** Full CRUD + search + booking flow works via `/docs`, with JWT auth enforced and a real race-condition test passing.

---

## 5. Background Jobs — Celery + Redis (Local)

**Learn:**
- Celery task definition, `delay()`/`apply_async()`, retries with backoff, task result backends.
- Redis as both broker and (optionally) result backend.
- Celery Beat for scheduled/periodic tasks.
- **FastAPI-compatible alternative worth knowing:** if you'd rather avoid Celery's heavier setup, **Dramatiq** or **arq** (asyncio-native, Redis-backed) are lighter-weight and integrate more naturally with FastAPI's async style. This plan uses Celery since it's the most transferable skill and has the clearest conceptual mapping to "independent Lambda functions" later, but arq is a reasonable substitute if you want less ceremony.

**Background jobs to build (each is a real feature, not a toy):**
1. **Booking confirmation notification** — on `POST /bookings`, enqueue a task that "sends" (log/print, or real email via a free SMTP sandbox like Mailtrap) a confirmation.
2. **Booking expiry** — a Celery Beat periodic task that cancels `PENDING` bookings older than N minutes and releases the held seats.
3. **Route-popularity cache warmup** — a periodic task that pre-computes and caches (in Redis) the most-searched source/destination pairs' results, so `POST /search` can check cache before hitting Postgres.
4. **Vehicle photo processing** — on upload, enqueue a task that generates a thumbnail and stores it back to MinIO (gives you a task with a real external I/O dependency, which matters later).

**Checkpoint:** All four jobs run correctly via `celery -A app.worker worker` and `celery -A app.worker beat`, observable via **Flower** (Celery's monitoring UI) for visibility into queue depth and task success/failure.

---

## 6. Pytest — Testing the Full Stack

**Do:**
- Unit tests for the matching algorithm (§3) — this deserves the heaviest test coverage since it's pure logic.
- Integration tests for booking + seat-concurrency: spin up two concurrent booking requests against the last seat and assert only one succeeds.
- Celery task tests using `task_always_eager=True` (runs tasks synchronously in tests, no broker needed) for fast unit tests, plus at least one true integration test against a real Redis test instance for the expiry job's timing logic.
- Auth/role tests: confirm a rider cannot hit driver-only endpoints and vice versa.

**Checkpoint:** `pytest -v` green, including the concurrency test — this is the test most worth demonstrating in a portfolio, since it shows you understand a subtle real-world bug class.

---

## 7. React Frontend (Local)

Keep this proportional — the backend is the learning focus, but the frontend needs to be real enough to exercise the API meaningfully.

**Build:**
- Auth pages (register/login), storing JWT (in memory or httpOnly cookie — avoid `localStorage` for anything security-sensitive if you want to demonstrate good practice).
- Driver flow: create vehicle → create route (pick source/destination/intermediate stops from an autocomplete backed by `GET /locations`) → schedule a trip.
- Rider flow: search form (source, destination, date, seats) → results list → book a trip.
- A basic "My Bookings" / "My Routes" dashboard.
- Use a simple state approach (React Query / TanStack Query for server state is a good, realistic choice) rather than hand-rolled fetch + `useState` everywhere.

**Checkpoint:** A rider can search and book, a driver can create a route and see bookings against their trips — full loop, hitting the real local API.

---

## 8. Dockerize — Same Architecture, Containerized

**Principle:** nothing architecturally changes here. If you find yourself redesigning anything at this stage, it means Stage 1 wasn't actually decoupled enough — go back and fix that instead of compensating in Docker.

**`docker-compose.yml` services:**
- `api` — FastAPI app
- `worker` — Celery worker (same image as `api`, different entrypoint command)
- `beat` — Celery beat scheduler (same image again)
- `redis` — broker + cache
- `postgres` — database
- `minio` — S3-compatible media storage
- `flower` — Celery monitoring UI
- `frontend` — React build served via nginx (or a dev-mode container for local iteration)

**Do:**
- One shared base image for `api`/`worker`/`beat` (same codebase, different `CMD`) — this mirrors how you'll later share one Lambda deployment package across multiple function roles.
- All config via environment variables (already true from the general-stack plan's Docker phase).
- Confirm the full docker-compose stack reproduces every checkpoint from §3–§7 with zero code changes — only infra/config changes.

**Checkpoint:** `docker compose up` gives a new developer the entire product — API, workers, scheduler, database (pre-seeded via the Alembic migrations running on startup), media storage, and frontend — with no manual steps.

---

## 9. The Cloud Pivot — Why Celery Doesn't Come With You

Before building Stage 3, understand *why* the architecture changes shape here, not just *that* it does:

- Celery workers are **long-running processes** that continuously poll a broker. Lambda functions are **short-lived, invoked-on-demand** — there's no equivalent to a persistent Celery worker process in Lambda.
- Celery Beat (the scheduler) has no direct Lambda equivalent either — its job (periodic triggering) is replaced by **EventBridge Scheduled Rules**, which invoke a Lambda directly on a cron schedule.
- The conceptual mapping you're implementing:

| Local/Docker (Stage 1–2) | Cloud (Stage 3) |
|---|---|
| Celery task function | Independent Lambda function |
| Redis (broker) | SQS queue |
| `task.delay()` call | `sqs.send_message()` call |
| Celery worker process polling Redis | SQS → Lambda event source mapping (AWS polls SQS and invokes Lambda for you) |
| Celery Beat periodic task | EventBridge Scheduled Rule → Lambda |
| Flower (monitoring) | CloudWatch Logs + Lambda metrics + SQS queue depth alarms |
| MinIO | Real S3 |
| Local Postgres | RDS Postgres (or Aurora Serverless if you want to explore scale-to-zero) |

Each of your four background jobs from §5 becomes its **own independently deployable Lambda function**, each triggered by its own SQS queue (or EventBridge rule, for the periodic expiry job). This is a genuine architectural improvement, not just a forced translation: independent scaling and independent failure isolation per job type is exactly what event-driven design is for.

---

## 10. Cloud-Native Build-Out

### 10.1 API on Lambda behind API Gateway
- Wrap the FastAPI app with **Mangum** (an ASGI adapter for Lambda) — this typically requires no changes to your route code, only a small handler shim.
- Package as a **container-image Lambda** (reuse your Docker image from Stage 2 with a Mangum entrypoint added) — this is a direct continuation of skills already built, not a new packaging model.
- Set up API Gateway (HTTP API, not REST API, for simplicity/cost) with a Lambda proxy integration.
- **Watch for:** Lambda + RDS connection-pooling issues (flagged back in the general-stack plan) — mitigate with small pool sizes or RDS Proxy.

### 10.2 Background jobs as independent Lambdas
- One Lambda per job (`notify-booking`, `expire-bookings`, `warm-search-cache`, `process-vehicle-photo`), each with its own IAM role scoped to only what it needs.
- `notify-booking`, `warm-search-cache`, `process-vehicle-photo` — triggered by their own SQS queue (with a DLQ each).
- `expire-bookings` — triggered by an EventBridge Scheduled Rule instead of SQS (it's periodic, not event-triggered).
- Update the API's booking/upload endpoints to call `sqs.send_message()` instead of `task.delay()`.

### 10.3 Media storage
- Point vehicle-photo uploads at real S3 instead of MinIO — since you built against the S3 API from the start (§4), this should be closer to a config change than a code change.
- Use presigned URLs for direct browser-to-S3 uploads if you want to go further (avoids routing large files through your API/Lambda at all — a genuinely better pattern worth the extra step).

### 10.4 Frontend on S3 + CloudFront
- Build the React app (`npm run build`), upload the static bundle to an S3 bucket configured for static website hosting.
- Put CloudFront in front of it for CDN caching and HTTPS.
- Point the frontend's API base URL at your API Gateway endpoint.

**Checkpoint:** The full product — search, book, upload a vehicle photo, receive an (SQS-triggered) confirmation, have a stale booking auto-expire — works end-to-end on AWS, with zero servers you manage directly.

---

## 11. CloudFormation — Codify Everything in §10

Only attempt this after §10 works via manual console setup — same rule as the general-stack plan: **build it by hand once, then codify what you already understand.**

**Templates to write:**
- Networking: VPC, subnets (if using RDS — Lambda in a VPC has its own cold-start/networking nuances worth learning deliberately).
- `RoutingApiStack` — API Gateway + main Lambda + IAM role.
- `WorkersStack` — the four job Lambdas + their SQS queues/DLQs + EventBridge rule for the periodic one.
- `DataStack` — RDS Postgres instance, S3 buckets (media + frontend), CloudFront distribution.
- Parameterize per environment (`dev`/`staging`) and keep secrets (DB credentials) in **Secrets Manager**, referenced from the templates — not hardcoded.

**Checkpoint:** `aws cloudformation deploy` from an empty AWS account section stands up the entire platform — API, five Lambdas, four queues, RDS, two S3 buckets, and CloudFront — with the Alembic seed migration run once as a post-deploy step (e.g., invoked manually or via a one-off Lambda/ECS task).

---

## 12. Polish & Portfolio Framing

- Document the architecture with a diagram showing both the Docker-stage and cloud-stage versions side by side — the contrast itself is a strong portfolio artifact, since it demonstrates you understand *why* the shapes differ, not just that they do.
- Write up the seat-concurrency race condition and how you tested/fixed it — a good, specific engineering story.
- Note the Celery→Lambda/SQS mapping table (§9) explicitly in your README; it's a common real interview topic ("how would you move background jobs to serverless") and you'll have a genuine answer instead of a theoretical one.

---

## Summary Table

| Stage | Compute | Broker/Queue | Media | Frontend hosting | DB |
|---|---|---|---|---|---|
| 1. Local | `uvicorn` process | Redis + Celery | Local disk / MinIO | Vite/CRA dev server | Local Postgres |
| 2. Dockerized | Same, containerized | Redis + Celery (containerized) | MinIO (containerized) | nginx container | Postgres container |
| 3. Cloud-native | Lambda (API) + Lambda (jobs) | SQS + EventBridge | S3 | S3 + CloudFront | RDS Postgres |

This plan assumes the general-stack learning plan from earlier (FastAPI/SQLAlchemy/Pytest/Docker/AWS/CloudFormation fundamentals) as background — this document is the applied, product-specific version of it.
