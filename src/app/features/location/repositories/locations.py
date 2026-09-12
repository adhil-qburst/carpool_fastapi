from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.location.domain.enums import LocationStatus
from app.features.location.models.location import Location


class LocationRepo:
    def create(
        self,
        session: Session,
        *,
        name: str,
        city: str,
        lat: Decimal | None = None,
        lng: Decimal | None = None,
        status: LocationStatus = LocationStatus.ACTIVE,
    ) -> Location:
        location = Location(
            name=name,
            city=city,
            lat=lat,
            lng=lng,
            status=status,
        )
        session.add(location)
        session.flush()
        return location

    def get_by_id(self, session: Session, location_id: UUID) -> Location | None:
        return session.get(Location, location_id)

    def get_by_id_for_update(
        self,
        session: Session,
        location_id: UUID,
    ) -> Location | None:
        return session.scalar(
            select(Location).where(Location.id == location_id).with_for_update()
        )

    def search(
        self,
        session: Session,
        *,
        text: str,
        limit: int = 20,
        offset: int = 0,
        status: LocationStatus | None = None,
    ) -> list[Location]:
        stmt = select(Location)
        cleaned_text = text.strip()
        if cleaned_text:
            pattern = f"%{cleaned_text}%"
            stmt = stmt.where(
                or_(
                    Location.name.ilike(pattern),
                    Location.city.ilike(pattern),
                )
            )
        if status is not None:
            stmt = stmt.where(Location.status == status)

        stmt = stmt.order_by(Location.name.asc()).limit(limit).offset(offset)
        return list(session.scalars(stmt).all())

    def count_search(
        self,
        session: Session,
        *,
        text: str,
        status: LocationStatus | None = None,
    ) -> int:
        stmt = select(func.count(Location.id))
        cleaned_text = text.strip()
        if cleaned_text:
            pattern = f"%{cleaned_text}%"
            stmt = stmt.where(
                or_(
                    Location.name.ilike(pattern),
                    Location.city.ilike(pattern),
                )
            )
        if status is not None:
            stmt = stmt.where(Location.status == status)
        return session.scalar(stmt) or 0

    def update(
        self,
        session: Session,
        location: Location,
        *,
        name: str | None = None,
        city: str | None = None,
        lat: Decimal | None = None,
        lng: Decimal | None = None,
        status: LocationStatus | None = None,
    ) -> Location:
        if name is not None:
            location.name = name
        if city is not None:
            location.city = city
        if lat is not None:
            location.lat = lat
        if lng is not None:
            location.lng = lng
        if status is not None:
            location.status = status
        session.flush()
        return location

    def delete(self, session: Session, location: Location) -> None:
        session.delete(location)
        session.flush()


def get_location_repo() -> LocationRepo:
    return LocationRepo()
