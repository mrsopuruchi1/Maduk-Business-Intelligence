# backend/services/plan_access.py

"""
Plan Feature Access Control
Maduk Business Intelligence SaaS Platform
Multi-Tenant (User ↔ Tenant ↔ Subscription)
"""
from datetime import datetime, timedelta 
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.subscription import Subscription
from backend.models.user import User
from backend.models.user_tenant import UserTenant


# ----------------------------------
# PLAN FEATURES DEFINITION
# ----------------------------------

PLAN_FEATURES = {
    "Starter": [
        "Data Upload",
        "Analysis",
        "Visualization",
        "Conclusions"
    ],
    "Professional": [
        "Data Upload",
        "Analysis",
        "Visualization",
        "Conclusions",
        "AI Predictions",
        "Revenue Forecast",
        "AI Chatbot",
        "PDF Reports"
    ],
    "Agency": [
        "Data Upload",
        "Analysis",
        "Visualization",
        "Conclusions",
        "AI Predictions",
        "Revenue Forecast",
        "AI Chatbot",
        "PDF Reports",
        "Budget Optimizer",
        "Growth Strategy Generator"
    ],
    "Enterprise": [
        "Data Upload",
        "Analysis",
        "Visualization",
        "Conclusions",
        "AI Predictions",
        "Revenue Forecast",
        "AI Chatbot",
        "PDF Reports",
        "Budget Optimizer",
        "Growth Strategy Generator",
        "Multi-Client Dashboards",
        "API Access",
        "Autonomous AI Consultant"
    ]
}

PLAN_ORDER = ["Starter", "Professional", "Agency", "Enterprise"]


# ----------------------------------
# FEATURES LOGIC
# ----------------------------------

def get_plan_features(plan: str) -> List[str]:
    if plan not in PLAN_ORDER:
        return []

    features = []

    for p in PLAN_ORDER:
        features.extend(PLAN_FEATURES.get(p, []))
        if p == plan:
            break

    return list(set(features))


def has_feature_access(plan: str, feature: str) -> bool:
    return feature in get_plan_features(plan)


def is_valid_plan(plan: str) -> bool:
    return plan in PLAN_FEATURES


def can_upgrade(current_plan: str, target_plan: str) -> bool:
    return PLAN_ORDER.index(target_plan) > PLAN_ORDER.index(current_plan)


def can_downgrade(current_plan: str, target_plan: str) -> bool:
    return PLAN_ORDER.index(target_plan) < PLAN_ORDER.index(current_plan)


# =========================================================
# 🔥 MULTI-TENANT LOGIC (FIXED)
# =========================================================

async def get_user_tenant_plan(
    db: AsyncSession,
    user_id: int,
    tenant_id: int
) -> str:
    """
    Get plan using UserTenant (source of truth)
    """

    result = await db.execute(
        select(UserTenant).where(
            UserTenant.user_id == user_id,
            UserTenant.tenant_id == tenant_id
        )
    )

    user_tenant = result.scalar_one_or_none()

    if not user_tenant:
        return "Starter"

    if user_tenant.subscription_expiry and user_tenant.subscription_expiry < datetime.utcnow():
        return "Starter"
    
    return user_tenant.subscription_plan or "Starter"
    


# ----------------------------------
# CHECK FEATURE ACCESS (MULTI-TENANT)
# ----------------------------------

async def has_tenant_feature_access(
    db: AsyncSession,
    user_id: int,
    tenant_id: int,
    feature: str
) -> bool:

    plan = await get_user_tenant_plan(db, user_id, tenant_id)

    return has_feature_access(plan, feature)


# ----------------------------------
# REQUIRE FEATURE (FOR ENDPOINTS)
# ----------------------------------

async def require_feature(
    db: AsyncSession,
    user_id: int,
    tenant_id: int,
    feature: str
):
    from fastapi import HTTPException

    allowed = await has_tenant_feature_access(
        db, user_id, tenant_id, feature
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade your plan to access '{feature}'"
        )


# =========================================================
# 🔗 PAYMENTS INTEGRATION (FIXED)
# =========================================================

async def activate_subscription(
    db: AsyncSession,
    user_tenant_id: int,
    plan: str,
    flutterwave_tx_id: str = None
):
    """
    Activate or update a subscription after successful payment.
    """

    # Fetch subscription for this user + tenant
    result = await db.execute(
        select(Subscription).where(Subscription.user_tenant_id == user_tenant.id)
    )
    subscription = result.scalars().first()

    now = datetime.utcnow()

    if subscription:
        # Update existing subscription
        subscription.plan = plan
        subscription.status = "active"
        subscription.flutterwave_subscription_id = flutterwave_tx_id

        if subscription.expiry_date and subscription.expiry_date > now:
            subscription.expiry_date += timedelta(days=30) 
        else:
            subscription.start_date = now
            subscription.expiry_date = now + timedelta(days=30) 
        
    else:
        # Create new subscription if it doesn't exist
        subscription = Subscription(
            user_tenant_id=user_tenant_id,
            plan=plan,
            status="active",
            flutterwave_subscription_id=flutterwave_tx_id,
            start_date=now,
            expiry_date=now + timedelta(days=30)
        )
        db.add(subscription)

    result = await db.execute(select(UserTenant).where(UserTenant.id == user_tenant.id))
    user_tenant = result.scalar_one_or_none()

    if user_tenant:
        user_tenant.subscription_plan = plan
        user_tenant.subscription_expiry = subscription.expiry_date
        db.add(user_tenant) 

    await db.commit()
    return subscription