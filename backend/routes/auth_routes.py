from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models.user import User
from backend.services.auth import verify_password, create_access_token, hash_password
from backend.services.tenant_service import create_tenant_service 

router = APIRouter(tags=["Auth"])


# -----------------------------
# SIGNUP
# -----------------------------
@router.post("/signup")
async def signup(
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # -----------------------------
        # CHECK IF USER EXISTS
        # -----------------------------
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # -----------------------------
        # CREATE USER
        # -----------------------------
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hash_password(password)
        )

        db.add(new_user)
        await db.flush()  # get ID

        # -----------------------------
        # CREATE DEFAULT TENANT
        # -----------------------------
        default_tenant = await create_tenant_service(
            db=db,
            user=new_user,
            tenant_name=f"{first_name}_{new_user.id}_tenant"
        )

        # ❌ REMOVE extra commit (service already commits)
        # await db.commit()

        # -----------------------------
        # CREATE JWT TOKEN (FIXED)
        # -----------------------------
        access_token = create_access_token(
            data={"sub": new_user.email}  # ✅ FIX
        )

        return {
            "status": "success",
            "message": "User registered successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "tenant_id": default_tenant["tenant_id"]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    try:
        # -----------------------------
        # FETCH USER
        # -----------------------------
        result = await db.execute(
            select(User).where(User.email == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # -----------------------------
        # CREATE JWT TOKEN (CONSISTENT)
        # -----------------------------
        access_token = create_access_token(
            data={"sub": user.email}  # ✅ MUST MATCH SIGNUP
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))