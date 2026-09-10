from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.features.auth.exceptions import (
    EmailAlreadyRegisteredError,
    EmailDeliveryError,
    EmailNotFoundError,
    InvalidCredentialError,
    InvalidEmailVerificationTokenError,
    InvalidRefreshTokenError,
    RegisteredUserError,
    UnVerifiedUserError,
    UserDisabledError,
)
from app.features.auth.schemas.login import LoginRequest, LoginResponse
from app.features.auth.schemas.refresh_token import (
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.features.auth.schemas.register import RegisterRequest, RegisterResponse
from app.features.auth.services.login import login_with_email_password
from app.features.auth.services.refresh_token import refresh_access_token
from app.features.auth.services.register import register_user
from app.features.auth.services.verify_email import verify_email as verify_user_email

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
    except RegisteredUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        ) from exc

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
    )


@router.get(
    "/verify-email",
    status_code=status.HTTP_303_SEE_OTHER,
)
def verify_email(
    token: UUID = Query(..., description="Email verification token."),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        verify_user_email(db, token)
    except InvalidEmailVerificationTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc

    return RedirectResponse(
        url=get_settings().email_verification_success_url,
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/login", status_code=status.HTTP_200_OK, response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    try:
        tokens = login_with_email_password(
            session=db, email=payload.email, password=payload.password
        )
        return LoginResponse(
            access_token=tokens.access_token, refresh_token=tokens.refresh_token
        )

    except InvalidCredentialError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc

    except EmailNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc

    except UserDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc

    except UnVerifiedUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.detail,
        ) from exc

    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        ) from exc


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=RefreshTokenResponse,
)
def refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> RefreshTokenResponse:
    try:
        tokens = refresh_access_token(
            session=db,
            refresh_token=payload.refresh_token,
        )
        return RefreshTokenResponse(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in or 900,
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
        ) from exc
    except UserDisabledError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
        ) from exc
    except UnVerifiedUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
        ) from exc
