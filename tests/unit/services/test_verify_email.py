from types import SimpleNamespace
from uuid import UUID

import pytest

from app.core.security.verification_token import hash_token
from app.features.auth.exceptions import InvalidEmailVerificationTokenError
from app.features.auth.services import verify_email as verify_email_service
from app.features.users.domain.enums import UserStatus


class FakeSession:
    def __init__(self):
        self.began = False

    def begin(self):
        return self

    def __enter__(self):
        self.began = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_verify_email_activates_user_and_marks_token_used(monkeypatch):
    session = FakeSession()
    token = UUID("4d0f14da-3c78-4247-8b97-70450dfc3e85")
    verification_token = SimpleNamespace(user_id="user-id", used_at=None)
    user = SimpleNamespace(is_email_verified=False, status=UserStatus.PENDING)
    captured = {}

    def get_active_token(received_session, token_hash):
        captured["session"] = received_session
        captured["token_hash"] = token_hash
        return verification_token

    monkeypatch.setattr(
        verify_email_service.token_repo,
        "get_active_by_hash_for_update",
        get_active_token,
    )
    monkeypatch.setattr(
        verify_email_service.users_repo,
        "get_by_id",
        lambda received_session, user_id: user,
    )

    verify_email_service.verify_email(session, token)

    assert session.began is True
    assert captured == {"session": session, "token_hash": hash_token(str(token))}
    assert user.is_email_verified is True
    assert user.status is UserStatus.ACTIVE
    assert verification_token.used_at is not None


def test_verify_email_rejects_missing_token_without_updating_user(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(
        verify_email_service.token_repo,
        "get_active_by_hash_for_update",
        lambda received_session, token_hash: None,
    )

    with pytest.raises(InvalidEmailVerificationTokenError):
        verify_email_service.verify_email(
            session,
            UUID("4d0f14da-3c78-4247-8b97-70450dfc3e85"),
        )

    assert session.began is True
