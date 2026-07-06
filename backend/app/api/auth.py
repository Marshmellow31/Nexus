"""Auth routes — /me endpoint for profile + settings."""

from fastapi import APIRouter, Depends

from app.api.schemas import UserOut
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
