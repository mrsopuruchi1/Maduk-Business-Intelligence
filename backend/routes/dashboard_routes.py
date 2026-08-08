# backend/routes/dashboard_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.services.auth import get_current_user
from backend.models.user import User
from backend.models.tenant import Tenant
from backend.models.user_tenant import UserTenant  # association table
from backend.utils.auth import get_current_user_tenant 

import aioredis
import os

router = APIRouter(
    prefix="",
    tags=["Dashboard"]
)

# ----------------------------
# REDIS SETUP (SAFE FALLBACK)
# ----------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
except:
    redis = None


# ----------------------------
# DASHBOARD ENDPOINT
# ----------------------------
@router.get("/dashboard", name="get_dashboard")
async def dashboard(
    context: dict = Depends(get_current_user_tenant),
    db: AsyncSession = Depends(get_db)
):
    user = context["user"]
    tenant = context["tenant"] 
    user_tenant = context["UserTenant"] 
    # Get user
    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none() 

    # Get tenant
    ut_result = await db.execute(
        select(UserTenant).where(UserTenant.user_id == user.id)
    )
    user_tenant = ut_result.scalars().first()

    if not user_tenant:
        return {"message": "No tenant found"}

    # Tenant-aware data
    data = {
        "tenant_id": user_tenant.tenant_id,
        "plan": user_tenant.subscription_plan,
        "features": get_plan_features(user_tenant.subscription_plan),
        "dashboard": {
            "total_clients": 120,
            "active_campaigns": 25,
            "monthly_revenue": 50000
        }
    }

    return data

    # ----------------------------
    # VERIFY USER BELONGS TO TENANT
    # ----------------------------
    association_query = await db.execute(
        select(user_tenant).where(
            (user_tenant.c.user_id == user.id) &
            (user_tenant.c.tenant_id == tenant_id)
        )
    )

    association = association_query.first()

    if not association:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this tenant"
        )

    # ----------------------------
    # REDIS CACHE (SAFE)
    # ----------------------------
    cache_key = f"dashboard:{tenant_id}"

    try:
        if redis:
            cached = await redis.get(cache_key)
            if cached:
                return {
                    "tenant_id": tenant_id,
                    "source": "cache",
                    "data": cached
                }
    except:
        pass  # Redis offline → ignore

    # ----------------------------
    # GENERATE DASHBOARD DATA
    # ----------------------------
    # (Replace later with real analytics)
    dashboard_data = {
        "tenant_id": tenant_id,
        "total_clients": 120,
        "active_campaigns": 25,
        "monthly_revenue": 50000,
        "subscription_plan": association.subscription_plan,
        "user_role": association.role
    }

    # ----------------------------
    # CACHE RESULT (OPTIONAL)
    # ----------------------------
    try:
        if redis:
            await redis.set(cache_key, str(dashboard_data), ex=300)
    except:
        pass

    # ----------------------------
    # RETURN RESPONSE
    # ----------------------------
    return {
        "tenant_id": tenant_id,
        "source": "live",
        "data": dashboard_data
    }