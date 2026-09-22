from uuid import UUID

from app.db.session import Session
from app.features.notifications.domain.enums import NotificationType
from app.features.notifications.repositories.notifications import \
    get_notification_repo
from app.features.ride_preferences.repositories.ride_preferences import \
    get_ride_preference_repo
from app.features.routes.models.route_stop import RouteStop
from app.features.trips.domain.enums import TripStatus
from app.features.trips.repositories.trips import get_trip_repo


def process_trip_created_notification(session: Session, trip_id: UUID):

    trip = get_trip_repo().get_by_id(session=session, trip_id=trip_id)
    if not trip:
        return
    
    if trip.status != TripStatus.SCHEDULED:
        return
    
    if not trip.route or not trip.route.route_stops:
                return
    
    sorted_stops : list[RouteStop] = sorted(trip.route.route_stops, key=lambda s:s.sequence)
    
    if len(sorted_stops) < 2:
                return
            
    source_stop = sorted_stops[0]
    dest_stop = sorted_stops[-1]
    
    ride_prefs = get_ride_preference_repo().list_active_by_locations(session=session,
                                                                        source_location_id=source_stop.location_id,
                                                                        destination_location_id=dest_stop.location_id)
    
    if not ride_prefs:
        return
    
    notification_repo = get_notification_repo()
    
    source_name = source_stop.location.name
    dest_name = dest_stop.location.name
    time_str = trip.departure_date.strftime("%I:%M %p")

    title = f"New Ride Match: {source_name} to {dest_name}"
    message = (
            f"A new ride matching your route preference from {source_name} to {dest_name} "
            f"has been scheduled for {trip.departure_date} at {time_str}."
        )
    
    for ride_pref in ride_prefs:
        data = {'trip_id': str(trip_id) }
        notification_repo.create(session=session,
                                    title=title,
                                    message=message,
                                    user_id=ride_pref.rider_id,
                                    type=NotificationType.TRIP_CREATED,
                                    data=data
                                    )
        
        