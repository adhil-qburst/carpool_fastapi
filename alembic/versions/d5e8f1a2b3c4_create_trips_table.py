"""create trips table

Revision ID: d5e8f1a2b3c4
Revises: 7114d32f3cb5
Create Date: 2026-09-14 17:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e8f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "7114d32f3cb5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    trip_status = sa.Enum("scheduled", "cancelled", "completed", name="trip_status")
    trip_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "trips",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("route_id", sa.UUID(), nullable=False),
        sa.Column("driver_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("departure_date", sa.Date(), nullable=False),
        sa.Column("departure_time", sa.Time(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            trip_status,
            server_default="scheduled",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trips_departure_date"), "trips", ["departure_date"], unique=False
    )
    op.create_index(
        op.f("ix_trips_driver_id"), "trips", ["driver_id"], unique=False
    )
    op.create_index(
        op.f("ix_trips_route_id"), "trips", ["route_id"], unique=False
    )
    op.create_index(
        op.f("ix_trips_vehicle_id"), "trips", ["vehicle_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trips_vehicle_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_route_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_driver_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_departure_date"), table_name="trips")
    op.drop_table("trips")
    sa.Enum("scheduled", "cancelled", "completed", name="trip_status").drop(
        op.get_bind(), checkfirst=True
    )

