from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.user_tenant import UserTenant
from backend.utils.auth import get_current_user  # ✅ FIXED IMPORT
from backend.services.tenant_service import create_tenant_service
from backend.services.membership_service import change_role_service

router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"]
)

# ----------------------------
# Pydantic Schemas
# ----------------------------
class TenantCreateRequest(BaseModel):
    name: str

class TenantResponse(BaseModel):
    tenant_id: int
    name: str
    role: str
    subscription_plan: str


# ----------------------------
# CREATE TENANT
# ----------------------------
@router.post("/create")
async def create_tenant(
    request: TenantCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ FIXED
):
    try:
        tenant = await create_tenant_service(
            db=db,
            user=user,
            tenant_name=request.name
        )

        return tenant  # ✅ REMOVED EXTRA COMMIT

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------
# ADD MEMBER
# ----------------------------
@router.post("/members/add")
async def add_member(
    tenant_id: int,
    target_user_id: int,
    role: str,
    user: User = Depends(get_current_user),  # ✅ FIXED
    db: AsyncSession = Depends(get_db)
):
    from backend.services.membership_service import add_member_service

    return await add_member_service(
        db,
        tenant_id,
        target_user_id,
        role,
        user.id  # ✅ FIXED
    )


# ----------------------------
# LIST TENANTS
# ----------------------------
@router.get("/list")
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ FIXED
):
    try:
        result = await db.execute(
            select(Tenant)
            .join(UserTenant, Tenant.id == UserTenant.tenant_id)
            .where(UserTenant.user_id == user.id)
        )

        tenants = result.scalars().all()

        return [
            {
                "tenant_id": t.id,
                "name": t.name
            }
            for t in tenants
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------
# LIST MEMBERS
# ----------------------------
@router.get("/members/list")
async def list_tenant_members(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # ----------------------------
    # CHECK ACCESS
    # ----------------------------
    access = await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id
        )
    )

    user_tenant = access.scalar_one_or_none()

    if not user_tenant:
        raise HTTPException(status_code=403, detail="Access denied")

    # ----------------------------
    # GET ALL MEMBERS (FIXED)
    # ----------------------------
    result = await db.execute(
        select(UserTenant)
        .options(selectinload(UserTenant.user))
        .where(UserTenant.tenant_id == tenant_id)
    )

    members = result.scalars().all()

    # ----------------------------
    # FORMAT RESPONSE
    # ----------------------------
    output = []

    for m in members:
        name = f"{m.user.first_name} {m.user.last_name}".title()

        output.append({
            "name": name if name else "N/A",
            "email": m.user.email,
            "user_id": m.user_id,
            "tenant_id": m.tenant_id,
            "role": m.role,
            "is_owner": m.role == "Owner"  # ✅ FIXED
        })

    return output


# ----------------------------
# CHANGE ROLE
# ----------------------------
@router.post("/members/change-role")
async def change_role(
    tenant_id: int,
    target_user_id: int,
    new_role: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)  # ✅ FIXED
):
    try:
        return await change_role_service(
            db,
            tenant_id,
            target_user_id,
            new_role,
            user.id  # ✅ FIXED
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.delete("/members/remove")
async def remove_member(
    tenant_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # 🔍 Get current user from DB
        result = await db.execute(
            select(User).where(User.email == user.email)
        )
        current_user = result.scalar_one_or_none()

        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # 🔧 Import service
        from backend.services.membership_service import remove_member_service

        return await remove_member_service(
            db,
            tenant_id,
            target_user_id,
            current_user.id
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))