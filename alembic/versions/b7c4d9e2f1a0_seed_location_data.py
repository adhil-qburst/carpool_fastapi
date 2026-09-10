"""Seed location data

Revision ID: b7c4d9e2f1a0
Revises: 86ee3686b1b3
Create Date: 2026-09-09 17:30:00.000000

"""

import json
import uuid
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c4d9e2f1a0"
down_revision: Union[str, Sequence[str], None] = "86ee3686b1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _load_location_seed_data() -> list[dict[str, object]]:
    seed_path = Path(__file__).resolve().parents[2] / (
        "src/seeds/data/kozhikode_locations.json"
    )
    with seed_path.open("r", encoding="utf-8") as file:
        locations = json.load(file)

    return [
        {
            "id": uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"location:{location['city']}:{location['name']}",
            ),
            "name": location["name"],
            "city": location["city"],
            "lat": location.get("lat"),
            "lng": location.get("lng"),
        }
        for location in locations
    ]


def upgrade() -> None:
    """Seed the location table."""
    locations = sa.table(
        "locations",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String(length=255)),
        sa.column("city", sa.String(length=255)),
        sa.column("lat", sa.Numeric()),
        sa.column("lng", sa.Numeric()),
    )
    op.bulk_insert(locations, _load_location_seed_data())


def downgrade() -> None:
    """Remove the seeded locations."""
    locations = sa.table("locations", sa.column("id", sa.UUID()))
    seed_ids = [row["id"] for row in _load_location_seed_data()]
    op.execute(locations.delete().where(locations.c.id.in_(seed_ids)))