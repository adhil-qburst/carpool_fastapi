"""Side-effect import of every feature's SQLAlchemy models.

Import this module (not the individual feature model modules) before any code
that configures mappers or builds a Session, so relationship() string
references (e.g. Mapped["Vehicle"]) can always be resolved regardless of
which entrypoint (API, dramatiq worker, script, REPL) runs first.
"""

from app.features.location.models.location import Location
from app.features.routes.models.route import Route
from app.features.routes.models.route_stop import RouteStop
from app.features.users.models.email_verification_token import EmailVerificationToken
from app.features.users.models.user import User
from app.features.vehicles.models.vehicle import Vehicle
from app.features.trips.models.trip import Trip
from app.features.bookings.models.booking import Booking
from app.features.ride_preferences.models.ride_preference import RidePreference
from app.features.notifications.models.notification import Notification

__all__ = [
    "Location",
    "Route",
    "RouteStop",
    "EmailVerificationToken",
    "User",
    "Vehicle",
    "Trip",
    "Booking",
    "RidePreference",
    "Notification",
]
