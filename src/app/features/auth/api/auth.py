from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredError, EmailDeliveryError
from app.db.session import get_db
from app.features.auth.schemas.register import RegisterRequest, RegisterResponse
from app.features.auth.schemas.verify_email import VerifyEmailResponse
from app.features.users.services.register import register_user

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterResponse,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    try:
        register_user(db, payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.detail,
        ) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        ) from exc

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
    )


@router.get(
    "/verify-email",
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    token: UUID = Query(..., description="Email verification token."),
):
    return VerifyEmailResponse(
        message="Your email is verified, Please login to your account."
    )
