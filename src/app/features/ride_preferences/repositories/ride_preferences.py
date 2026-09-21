from datetime import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.features.ride_preferences.models.ride_preference import RidePreference


class RidePreferenceRepo:
    def create(
        self,
        session: Session,
        *,
        rider_id: UUID,
        source_location_id: UUID,
        destination_location_id: UUID,
        preferred_departure_time: time | None = None,
        seats_needed: int = 1,
        is_active: bool = True,
        label: str | None = None,
    ) -> RidePreference:
        preference = RidePreference(
            rider_id=rider_id,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            preferred_departure_time=preferred_departure_time,
            seats_needed=seats_needed,
            is_active=is_active,
            label=label,
        )
        session.add(preference)
        session.flush()
        return preference

    def get_by_id(
        self,
        session: Session,
        ride_preference_id: UUID,
    ) -> RidePreference | None:
        return session.get(RidePreference, ride_preference_id)

    def get_by_id_for_update(
        self,
        session: Session,
        ride_preference_id: UUID,
    ) -> RidePreference | None:
        return session.scalar(
            select(RidePreference)
            .where(RidePreference.id == ride_preference_id)
            .with_for_update()
        )

    def get_by_id_with_details(
        self,
        session: Session,
        ride_preference_id: UUID,
    ) -> RidePreference | None:
        return session.scalar(
            select(RidePreference)
            .where(RidePreference.id == ride_preference_id)
            .options(
                joinedload(RidePreference.rider),
                joinedload(RidePreference.source),
                joinedload(RidePreference.destination),
            )
        )

    def list_by_rider_id(
        self,
        session: Session,
        rider_id: UUID,
        *,
        active_only: bool = False,
    ) -> list[RidePreference]:
        stmt = (
            select(RidePreference)
            .where(RidePreference.rider_id == rider_id)
            .options(
                joinedload(RidePreference.source),
                joinedload(RidePreference.destination),
            )
        )
        if active_only:
            stmt = stmt.where(RidePreference.is_active.is_(True))
        stmt = stmt.order_by(RidePreference.created_at.desc())
        return list(session.scalars(stmt).unique().all())

    def get_active_by_rider_and_locations(
        self,
        session: Session,
        *,
        rider_id: UUID,
        source_location_id: UUID,
        destination_location_id: UUID,
    ) -> RidePreference | None:
        return session.scalar(
            select(RidePreference).where(
                RidePreference.rider_id == rider_id,
                RidePreference.source_location_id == source_location_id,
                RidePreference.destination_location_id == destination_location_id,
                RidePreference.is_active.is_(True),
            )
        )

    def list_active_by_locations(
        self,
        session: Session,
        *,
        source_location_id: UUID,
        destination_location_id: UUID,
    ) -> list[RidePreference]:
        return list(
            session.scalars(
                select(RidePreference)
                .where(
                    RidePreference.source_location_id == source_location_id,
                    RidePreference.destination_location_id == destination_location_id,
                    RidePreference.is_active.is_(True),
                )
                .options(
                    joinedload(RidePreference.rider),
                    joinedload(RidePreference.source),
                    joinedload(RidePreference.destination),
                )
                .order_by(RidePreference.created_at.desc())
            ).unique().all()
        )

    def update(
        self,
        session: Session,
        ride_preference: RidePreference,
        *,
        source_location_id: UUID | None = None,
        destination_location_id: UUID | None = None,
        preferred_departure_time: time | None = None,
        seats_needed: int | None = None,
        is_active: bool | None = None,
        label: str | None = None,
    ) -> RidePreference:
        if source_location_id is not None:
            ride_preference.source_location_id = source_location_id
        if destination_location_id is not None:
            ride_preference.destination_location_id = destination_location_id
        if preferred_departure_time is not None:
            ride_preference.preferred_departure_time = preferred_departure_time
        if seats_needed is not None:
            ride_preference.seats_needed = seats_needed
        if is_active is not None:
            ride_preference.is_active = is_active
        if label is not None:
            ride_preference.label = label
        session.flush()
        return ride_preference

    def delete(
        self,
        session: Session,
        ride_preference: RidePreference,
    ) -> None:
        session.delete(ride_preference)
        session.flush()


def get_ride_preference_repo() -> RidePreferenceRepo:
    return RidePreferenceRepo()
