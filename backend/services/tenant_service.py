from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from backend.models.tenant import Tenant
from backend.models.user_tenant import UserTenant
from backend.models.subscription import Subscription


async def create_tenant_service(db: AsyncSession, user, tenant_name: str):
    """
    Create tenant + assign Owner + create Starter subscription
    Multi-tenant safe + data isolation ready
    """

    tenant_name = tenant_name.strip()

    if not tenant_name:
        raise ValueError("Tenant name cannot be empty")

    # Prevent duplicate tenant name for same user
    existing = await db.execute(
        select(Tenant).where(
            Tenant.name == tenant_name,
            Tenant.owner_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("You already have a tenant with this name")

    try:
        # -----------------------------
        # CREATE TENANT
        # -----------------------------
        tenant = Tenant(
            name=tenant_name,
            owner_id=user.id
        )
        db.add(tenant)
        await db.flush()

        # -----------------------------
        # LINK USER → TENANT (OWNER)
        # -----------------------------
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=tenant.id,
            role="Owner",
            subscription_plan="Starter",
            subscription_expiry=None
        )
        db.add(user_tenant)
        await db.flush()

        # -----------------------------
        # CREATE SUBSCRIPTION (STARTER)
        # -----------------------------
        subscription = Subscription(
            user_id=user.id,
            tenant_id=tenant.id,
            user_email=user.email,
            user_tenant_id=user_tenant.id,
            plan="Starter",
            status="active",
            currency="USD",
            amount=0,
            start_date=datetime.utcnow(),
            expiry_date=None
        )
        db.add(subscription)

        # ✅ 🔥 CRITICAL FIX — COMMIT HERE
        await db.commit()

        return {
            "tenant_id": tenant.id,
            "name": tenant.name,
            "role": "Owner",
            "subscription_plan": "Starter"
        }

    except IntegrityError:
        await db.rollback()  # ✅ FIX
        raise ValueError("Tenant creation failed due to duplicate or constraint error")

    except Exception as e:
        await db.rollback()  # ✅ FIX
        raise Exception(f"Unexpected error: {str(e)}")