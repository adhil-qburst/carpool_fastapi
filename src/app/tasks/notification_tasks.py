
from uuid import UUID
from app.db.session import get_db_context
from app.features.trips.services.process_trip_created_notiifcation import process_trip_created_notification

import dramatiq

@dramatiq.actor(queue_name="trip_created_notification")
def process_trip_notification_task(trip_id: str | UUID) -> None:

    resolved_trip_id = UUID(str(trip_id))
    with get_db_context() as session:
        try:
            process_trip_created_notification(session=session, trip_id=resolved_trip_id)
            session.commit()
        except Exception as e:
            print(f"Error processing trip notification for trip_id {trip_id}: {e}")
            session.rollback()
            raise