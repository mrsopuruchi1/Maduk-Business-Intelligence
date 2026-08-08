# backend/services/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()

# -----------------------
# JWT SETTINGS
# -----------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

# ✅ USE ONLY THIS (NOT HTTPBearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -----------------------
# PASSWORD HELPERS
# -----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# -----------------------
# JWT HELPERS
# -----------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates JWT token
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -----------------------
# CURRENT USER
# -----------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Extract user email from JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    print("Token received:", token)  # Debug

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

        return user_id 

    except JWTError:
        raise credentials_exception


# -----------------------
# CURRENT TENANT (OPTIONAL)
# -----------------------
async def get_current_tenant(token: str = Depends(oauth2_scheme)) -> int:
    """
    Extract tenant_id from JWT (optional use)
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid token",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id = payload.get("tenant_id")

        if tenant_id is None:
            raise credentials_exception

        return tenant_id

    except JWTError:
        raise credentials_exception