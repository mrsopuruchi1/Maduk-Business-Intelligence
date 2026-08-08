import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from backend.database import get_db
from backend.models.user import User
from backend.models.user_tenant import UserTenant

# -----------------------------
# JWT SETTINGS
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -----------------------------
# TOKEN UTILS
# -----------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------------
# USER HELPERS
# -----------------------------
async def get_user_by_email(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# -----------------------------
# CURRENT USER
# -----------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(email, db)

    if not user:
        raise credentials_exception

    return user


# -----------------------------
# CURRENT USER + TENANT (FIXED CORE)
# -----------------------------
async def get_current_user_tenant(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserTenant:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # -----------------------------
    # GET USER
    # -----------------------------
    user_result = await db.execute(
        select(User).where(User.email == email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    # -----------------------------
    # GET ALL USER TENANTS
    # -----------------------------
    ut_result = await db.execute(
        select(UserTenant)
        .where(UserTenant.user_id == user.id)
        .order_by(UserTenant.id.asc())
    )

    user_tenants = ut_result.scalars().all()

    if not user_tenants:
        raise HTTPException(
            status_code=404,
            detail="No tenant found for this user"
        )

    # -----------------------------
    # SAFE DEFAULT SELECTION
    # -----------------------------
    user_tenant = next(
        (ut for ut in user_tenants if getattr(ut, "is_default", False)),
        user_tenants[0]
    )

    return user_tenant


# -----------------------------
# OPTIONAL TENANT CHECK
# -----------------------------
async def get_current_tenant(
    tenant_id: int,
    user_tenant: UserTenant = Depends(get_current_user_tenant)
):

    if user_tenant.tenant_id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied for this tenant"
        )

    return user_tenant