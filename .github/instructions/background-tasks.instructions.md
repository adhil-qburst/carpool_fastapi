---
name: Background Tasks (Dramatiq)
description: "Use when adding or modifying Dramatiq actors, the broker, or the worker entrypoint under src/app/tasks."
applyTo: "src/app/tasks/**/*.py"
---

# Background Tasks (Dramatiq)

- There is a single shared broker in [broker.py](../../src/app/tasks/broker.py): a
  `RabbitmqBroker` built from `get_settings().rabbitmq_url` and registered globally via
  `dramatiq.set_broker(broker)`. Don't create additional brokers.
- Group actors by domain in a `<feature>_tasks.py` file (e.g. `email_tasks.py`). Each actor is a
  thin `@dramatiq.actor(queue_name="<queue>")`-decorated function that delegates to a plain
  function in `core/` or a feature module — keep business/IO logic out of the actor body itself.
- Enqueue work from a `services/` function with `<task_name>.send(*args)`; never invoke the
  decorated function directly except from the actor's own queue consumer or in tests.
- [worker.py](../../src/app/tasks/worker.py) is the dramatiq entrypoint
  (`uv run dramatiq app.tasks.worker`): it must import `app.tasks.broker` for its side effect of
  registering the broker, and import every `*_tasks` module so its actors get registered. When you
  add a new `<feature>_tasks.py`, add its import here too.
- Task function arguments must be JSON-serializable (ids, strings, primitives) — pass ids/emails,
  not ORM model instances or `Session` objects.
