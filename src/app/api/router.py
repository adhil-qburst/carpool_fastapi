from fastapi import APIRouter

from app.features.auth.api import auth
from app.features.location.api import locations
from app.features.routes.api import routes
from app.features.trips.api import trips
from app.features.users.api import users
from app.features.vehicles.api import vehicles

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(routes.router, prefix="/routes", tags=["Routes"])
api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
api_router.include_router(users.router, prefix="/users", tags=["Auth"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
