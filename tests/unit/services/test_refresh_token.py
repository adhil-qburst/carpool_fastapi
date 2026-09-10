from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest

from app.core.security.jwt import JWTService
from app.features.auth.domain.entities.auth_token import RefreshedToken
from app.features.auth.domain.rules import ensure_user_is_active
from app.features.auth.exceptions import (
    InvalidRefreshTokenError,
    UnVerifiedUserError,
    UserDisabledError,
)
from app.features.auth.services import refresh_token as refresh_token_service
from app.features.users.domain.enums import UserStatus


class FakeSession:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def fake_settings():
    return SimpleNamespace(
        jwt_secret="unit-test-secret-key-32-chars-long!",
        jwt_refresh_secret="unit-test-refresh-secret-key-32!!",
        jwt_algorithm="HS256",
    )


@pytest.fixture
def jwt_service(fake_settings):
    return JWTService(
        secret_key=fake_settings.jwt_secret,
        refresh_secret_key=fake_settings.jwt_refresh_secret,
        algorithm=fake_settings.jwt_algorithm,
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


# =============================================================================
# Domain Rule: ensure_user_is_active
# =============================================================================


def test_ensure_user_is_active_passes_for_active_user():
    user = SimpleNamespace(status=UserStatus.ACTIVE)
    ensure_user_is_active(user)


def test_ensure_user_is_active_raises_when_disabled():
    user = SimpleNamespace(status=UserStatus.DISABLED)
    with pytest.raises(UserDisabledError) as exc_info:
        ensure_user_is_active(user)
    assert exc_info.value.code == "USER_DISABLED"
    assert exc_info.value.detail == "User account is disabled."


# =============================================================================
# Service: refresh_access_token
# =============================================================================


def test_refresh_access_token_success(monkeypatch, fake_settings, jwt_service):
    session = FakeSession()
    user_id = uuid4()
    refresh_token = jwt_service.create_refresh_token(user_id=user_id)

    fake_user = SimpleNamespace(
        id=user_id,
        email="test@example.com",
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, uid: fake_user if uid == user_id else None,
    )
    monkeypatch.setattr(refresh_token_service, "get_user_repo", lambda: fake_repo)

    result = refresh_token_service.refresh_access_token(
        session,
        refresh_token,
        settings=fake_settings,
    )

    assert isinstance(result, RefreshedToken)
    assert result.token_type == "bearer"
    assert result.expires_in == 900
    assert session.rolled_back is False

    payload = jwt_service.validate_access_token(result.access_token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_refresh_access_token_invalid_jwt_raises_error(fake_settings):
    session = FakeSession()

    with pytest.raises(InvalidRefreshTokenError) as exc_info:
        refresh_token_service.refresh_access_token(
            session,
            "not-a-valid-jwt-token",
            settings=fake_settings,
        )

    assert exc_info.value.code == "INVALID_REFRESH_TOKEN"
    assert session.rolled_back is True


def test_refresh_access_token_wrong_token_type_raises_error(fake_settings, jwt_service):
    session = FakeSession()
    user_id = uuid4()
    access_token = jwt_service.create_access_token(user_id=user_id)

    with pytest.raises(InvalidRefreshTokenError):
        refresh_token_service.refresh_access_token(
            session,
            access_token,
            settings=fake_settings,
        )

    assert session.rolled_back is True


def test_refresh_access_token_invalid_sub_raises_error(fake_settings):
    session = FakeSession()

    token = jwt.encode(
        {"sub": "not-a-valid-uuid", "type": "refresh"},
        fake_settings.jwt_refresh_secret,
        algorithm=fake_settings.jwt_algorithm,
    )

    with pytest.raises(InvalidRefreshTokenError):
        refresh_token_service.refresh_access_token(
            session,
            token,
            settings=fake_settings,
        )

    assert session.rolled_back is True


def test_refresh_access_token_user_not_found_raises_error(
    monkeypatch, fake_settings, jwt_service
):
    session = FakeSession()
    user_id = uuid4()
    refresh_token = jwt_service.create_refresh_token(user_id=user_id)

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, uid: None,
    )
    monkeypatch.setattr(refresh_token_service, "get_user_repo", lambda: fake_repo)

    with pytest.raises(InvalidRefreshTokenError) as exc_info:
        refresh_token_service.refresh_access_token(
            session,
            refresh_token,
            settings=fake_settings,
        )

    assert exc_info.value.code == "INVALID_REFRESH_TOKEN"
    assert session.rolled_back is True


def test_refresh_access_token_disabled_user_raises_error(
    monkeypatch, fake_settings, jwt_service
):
    session = FakeSession()
    user_id = uuid4()
    refresh_token = jwt_service.create_refresh_token(user_id=user_id)

    fake_user = SimpleNamespace(
        id=user_id,
        email="test@example.com",
        status=UserStatus.DISABLED,
        is_email_verified=True,
    )

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, uid: fake_user if uid == user_id else None,
    )
    monkeypatch.setattr(refresh_token_service, "get_user_repo", lambda: fake_repo)

    with pytest.raises(UserDisabledError) as exc_info:
        refresh_token_service.refresh_access_token(
            session,
            refresh_token,
            settings=fake_settings,
        )

    assert exc_info.value.code == "USER_DISABLED"
    assert session.rolled_back is True


def test_refresh_access_token_unverified_email_raises_error(
    monkeypatch, fake_settings, jwt_service
):
    session = FakeSession()
    user_id = uuid4()
    refresh_token = jwt_service.create_refresh_token(user_id=user_id)

    fake_user = SimpleNamespace(
        id=user_id,
        email="unverified@example.com",
        status=UserStatus.ACTIVE,
        is_email_verified=False,
    )

    fake_repo = SimpleNamespace(
        get_by_id=lambda s, uid: fake_user if uid == user_id else None,
    )
    monkeypatch.setattr(refresh_token_service, "get_user_repo", lambda: fake_repo)

    with pytest.raises(UnVerifiedUserError) as exc_info:
        refresh_token_service.refresh_access_token(
            session,
            refresh_token,
            settings=fake_settings,
        )

    assert exc_info.value.code == "UNVERIFIED_USER"
    assert exc_info.value.user_id == user_id
    assert exc_info.value.email == "unverified@example.com"
    assert session.rolled_back is True
