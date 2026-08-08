# backend/utils/helpers.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.user_tenant import user_tenant
from backend.models.subscription import Subscription
from typing import List, Optional

# -----------------------------
# USER HELPERS
# -----------------------------
async def get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    """Fetch a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_tenants(user_email: str, db: AsyncSession) -> List[dict]:
    """Fetch all tenants a user belongs to, with roles and subscriptions."""
    user = await get_user_by_email(user_email, db)
    if not user:
        return []

    stmt = select(user_tenant).where(user_tenant.c.user_id == user.id)
    associations = (await db.execute(stmt)).all()

    tenants_list = []
    for assoc in associations:
        tenant_id = assoc.user_tenant.tenant_id
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            tenants_list.append({
                "tenant_id": tenant.id,
                "name": tenant.name,
                "role": assoc.user_tenant.role,
                "subscription_plan": assoc.user_tenant.subscription_plan
            })
    return tenants_list


# -----------------------------
# TENANT HELPERS
# -----------------------------
async def get_tenant_by_id(tenant_id: int, db: AsyncSession) -> Optional[Tenant]:
    """Fetch a tenant by ID."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def get_tenant_users(tenant_id: int, db: AsyncSession) -> List[dict]:
    """Fetch all users belonging to a tenant."""
    stmt = select(user_tenant).where(user_tenant.c.tenant_id == tenant_id)
    associations = (await db.execute(stmt)).all()

    users_list = []
    for assoc in associations:
        user_id = assoc.user_tenant.user_id
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            users_list.append({
                "user_id": user.id,
                "email": user.email,
                "role": assoc.user_tenant.role,
                "subscription_plan": assoc.user_tenant.subscription_plan
            })
    return users_list


# -----------------------------
# SUBSCRIPTION HELPERS
# -----------------------------
async def get_subscription(user_email: str, tenant_id: int, db: AsyncSession) -> Optional[dict]:
    """Get subscription plan for a user under a specific tenant."""
    user = await get_user_by_email(user_email, db)
    if not user:
        return None

    stmt = select(user_tenant).where(
        (user_tenant.c.user_id == user.id) &
        (user_tenant.c.tenant_id == tenant_id)
    )
    assoc = (await db.execute(stmt)).first()
    if not assoc:
        return None

    return {
        "user_email": user.email,
        "tenant_id": tenant_id,
        "subscription_plan": assoc.user_tenant.subscription_plan,
        "role": assoc.user_tenant.role
    }


async def set_subscription_plan(user_email: str, tenant_id: int, plan: str, db: AsyncSession) -> bool:
    """Update subscription plan for a user under a tenant."""
    user = await get_user_by_email(user_email, db)
    if not user:
        return False

    stmt = select(user_tenant).where(
        (user_tenant.c.user_id == user.id) &
        (user_tenant.c.tenant_id == tenant_id)
    )
    assoc = (await db.execute(stmt)).first()
    if not assoc:
        return False

    await db.execute(
        user_tenant.update()
        .where(user_tenant.c.id == assoc.user_tenant.id)
        .values(subscription_plan=plan)
    )
    await db.commit()
    return True


# -----------------------------
# ROLE CHECK HELPERS
# -----------------------------
async def is_user_admin(user_email: str, tenant_id: int, db: AsyncSession) -> bool:
    """Check if a user is Admin for a specific tenant."""
    sub = await get_subscription(user_email, tenant_id, db)
    if not sub:
        return False
    return sub["role"].lower() == "admin"