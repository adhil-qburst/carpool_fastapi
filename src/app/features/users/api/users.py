from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security.dependencies import get_current_user_id
from app.db.session import get_db
from app.features.users.exceptions import UserNotFoundError
from app.features.users.schemas.current_user import CurrentUserResponse
from app.features.users.services.users import get_current_user

router = APIRouter()


@router.get("/current_user", response_model=CurrentUserResponse)
def current_user(
    db: Session = Depends(get_db), current_user_id: UUID = Depends(get_current_user_id)
) -> CurrentUserResponse:
    try:
        return get_current_user(session=db, user_id=current_user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
