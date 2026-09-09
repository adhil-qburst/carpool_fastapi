from fastapi import APIRouter

from app.features.auth.api import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
