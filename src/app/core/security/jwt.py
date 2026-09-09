from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError


class JWTService:
    def __init__(
        self,
        *,
        secret_key: str,
        refresh_secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.refresh_secret_key = refresh_secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, user_id: UUID) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expire_minutes
        )

        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def create_refresh_token(self, user_id: UUID) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            self.refresh_secret_key,
            algorithm=self.algorithm,
        )

    def validate_token(
        self,
        token: str,
        *,
        token_type: str,
        secret_key: str,
    ) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[self.algorithm],
            )
        except InvalidTokenError as exc:
            raise ValueError("Invalid or expired token") from exc

        if payload.get("type") != token_type:
            raise ValueError("Invalid token type")

        if not payload.get("sub"):
            raise ValueError("Token does not contain a user ID")

        return payload

    def validate_access_token(self, token: str) -> dict[str, Any]:
        return self.validate_token(
            token, token_type="access", secret_key=self.secret_key
        )

    def validate_refresh_token(self, token: str) -> dict[str, Any]:
        return self.validate_token(
            token, token_type="refresh", secret_key=self.refresh_secret_key
        )
