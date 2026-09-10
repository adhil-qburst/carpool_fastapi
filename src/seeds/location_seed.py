import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import get_session_factory
from app.features.location.models.location import Location

logger = logging.getLogger(__name__)

locations_path = ["src/seeds/data/kozhikode_locations.json"]


def seed_locations():

    for location_path in locations_path:

        logger.info("Seeding locations from %s", location_path)

        with Path(location_path).open("r", encoding="utf-8") as file:
            location_data = json.load(file)

        SessionLocal = get_session_factory()

        with SessionLocal() as db:
            created = 0
            skipped = 0

            for data in location_data:

                existing = db.scalar(
                    select(Location).where(
                        Location.name == data["name"],
                        Location.city == data["city"],
                    )
                )

                if existing is not None:
                    skipped += 1
                    continue

                db.add(
                    Location(
                        name=data["name"],
                        city=data["city"],
                        lat=data.get("lat"),
                        lng=data.get("lng"),
                    )
                )
                created += 1

            db.commit()

            logger.info(
                "Seeded %d new locations, skipped %d existing from %s",
                created,
                skipped,
                location_path,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_locations()
