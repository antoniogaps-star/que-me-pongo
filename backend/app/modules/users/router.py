"""Endpoints de usuarios. Por ahora, /users/me (perfil autenticado)."""

from uuid import UUID

from fastapi import APIRouter

from app.modules.users.models import User
from app.modules.users.schemas import UserRead
from app.shared.deps import Claims, TenantSession
from app.shared.errors import api_error

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(claims: Claims, session: TenantSession) -> User:
    # La sesión ya tiene el tenant fijado: RLS garantiza que solo veamos usuarios
    # de la propia empresa, incluso buscando por id.
    user = await session.get(User, UUID(claims["sub"]))
    if user is None:
        raise api_error(404, "USER_NOT_FOUND", "Usuario no encontrado")
    return user
