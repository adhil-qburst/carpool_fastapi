from fastapi import APIRouter

from app.features.auth.api import auth
from app.features.vehicles.api import vehicles

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])

