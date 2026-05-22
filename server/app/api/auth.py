from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse, TokenResponse, ChangePasswordRequest, UserUpdateRequest
from app.services.auth_service import authenticate_user, register_user, create_user_token
from app.middleware.auth import require_auth, require_admin
from app.models.user import User
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, req.username, req.password)
    token = create_user_token(user)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=UserResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await register_user(db, req.username, req.password, req.role)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(require_auth)):
    return UserResponse.model_validate(user)


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Change current user's password."""
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"message": "密码已修改"}


users_router = APIRouter(prefix="/users", tags=["用户管理"])


@users_router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update user info or reset password (admin only)."""
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.username is not None:
        existing = await db.execute(select(User).where(User.username == data.username, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")
        target.username = data.username
    if data.password is not None:
        target.password_hash = hash_password(data.password)
    if data.role is not None:
        target.role = data.role
    await db.commit()
    await db.refresh(target)
    return UserResponse.model_validate(target)


@users_router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete a user (admin only, cannot delete self)."""
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(target)
    await db.commit()
