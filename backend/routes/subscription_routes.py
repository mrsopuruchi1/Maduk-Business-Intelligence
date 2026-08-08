# backend/routes/subscription_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import select 
import httpx
import os 

from backend.database import get_db
from backend.models.user import User
from backend.models.user_tenant import UserTenant
from backend.models.subscription import Subscription
from backend.schemas.subscription_request import SubscriptionRequest
from backend.services.payments import create_flutterwave_subscription
from backend.utils.auth import get_current_user, get_current_user_tenant 

router = APIRouter(
    prefix="",
    tags=["Subscription"]
)

FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY") 

@router.post("/subscribe")
async def subscribe(
    request: SubscriptionRequest,
    user_tenant: UserTenant = Depends(get_current_user_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Subscribe a user to a plan (multi-tenant safe + idempotent)
    """

    print("UserTenant ID:", user_tenant.id, "Tenant ID:", user_tenant.tenant_id)

    # -----------------------------
    # GET USER (FIXED RELATION BUG)
    # -----------------------------
    result = await db.execute(
        select(User).where(User.id == user_tenant.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # -----------------------------
    # VALIDATE PLAN
    # -----------------------------
    valid_plans = ["Starter", "Professional", "Agency", "Enterprise"]

    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Choose from {valid_plans}"
        )

    # -----------------------------
    # STARTER PLAN (NO PAYMENT)
    # -----------------------------
    if request.plan == "Starter":
        user_tenant.subscription_plan = "Starter"
        user_tenant.subscription_expiry = None

        db.add(user_tenant)
        await db.commit()

        return {
            "status": "success",
            "message": "Starter plan activated",
            "tenant_id": user_tenant.tenant_id
        }

    # -----------------------------
    # VALIDATE CURRENCY
    # -----------------------------
    valid_currencies = ["USD", "NGN"]

    if request.currency not in valid_currencies:
        raise HTTPException(
            status_code=400,
            detail="Invalid currency. Use 'USD' or 'NGN'"
        )

    # -----------------------------
    # 🧠 IDENTITY SAFETY: CHECK EXISTING PENDING SUBSCRIPTION
    # -----------------------------
    existing = await db.execute(
        select(Subscription).where(
            Subscription.user_tenant_id == user_tenant.id,
            Subscription.plan == request.plan,
            Subscription.status == "pending"
        )
    )
    existing_subscription = existing.scalar_one_or_none()

    if existing_subscription and existing_subscription.tx_ref:
        # reuse existing payment session
        return {
            "status": "success",
            "user": user.email,
            "tenant_id": user_tenant.tenant_id,
            "plan": request.plan,
            "payment_link": f"https://checkout.flutterwave.com/v3/hosted/pay/{existing_subscription.tx_ref}"
        }

    try:
        # -----------------------------
        # CREATE PAYMENT SESSION
        # -----------------------------
        payment_data = await create_flutterwave_subscription(
            email=user.email,
            plan=request.plan,
            currency=request.currency,
            tenant_id=user_tenant.tenant_id,
            user_tenant_id=user_tenant.id
        )

        # -----------------------------
        # UPSERT SUBSCRIPTION RECORD (SAFE)
        # -----------------------------
        if existing_subscription:
            existing_subscription.tx_ref = payment_data["tx_ref"]
            subscription_record = existing_subscription
        else:
            subscription_record = Subscription(
                user_id=user.id,
                tenant_id=user_tenant.tenant_id,
                user_tenant_id=user_tenant.id,
                plan=request.plan,
                status="pending",
                start_date=datetime.utcnow(),
                tx_ref=payment_data["tx_ref"]
            )
            db.add(subscription_record)

        await db.commit()

        return {
            "status": "success",
            "user": user.email,
            "tenant_id": user_tenant.tenant_id,
            "plan": request.plan,
            "payment_link": payment_data["payment_link"]
        }

    except Exception as e:
        print("Subscription Error:", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Subscription creation failed: {str(e)}"
        )
    
@router.post("/cancel-subscription")
async def cancel_subscription(
    user_tenant: UserTenant = Depends(get_current_user_tenant),
    db: AsyncSession = Depends(get_db)
):
    # -----------------------------
    # FETCH SUBSCRIPTION
    # -----------------------------
    result = await db.execute(
        select(Subscription).where(Subscription.user_tenant_id == user_tenant.id)
    )
    subscription = result.scalars().first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if not subscription.flutterwave_subscription_id:
        raise HTTPException(status_code=400, detail="No active Flutterwave subscription")

    # -----------------------------
    # CANCEL ON FLUTTERWAVE
    # -----------------------------
    url = f"https://api.flutterwave.com/v3/subscriptions/{subscription.flutterwave_subscription_id}/cancel"

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, headers=headers)
        res_data = response.json()

    # -----------------------------
    # UPDATE SUBSCRIPTION (DOWNGRADE)
    # -----------------------------
    subscription.status = "cancelled"
    subscription.plan = "Starter"   # ✅ DOWNGRADE
    subscription.expiry_date = datetime.utcnow()  # optional: end immediately

    db.add(subscription)

    # -----------------------------
    # UPDATE USER-TENANT (IMPORTANT)
    # -----------------------------
    from backend.models.user_tenant import UserTenant

    result = await db.execute(
        select(UserTenant).where(UserTenant.id == user_tenant.id)
    )
    user_tenant = result.scalar_one_or_none()

    if user_tenant:
        user_tenant.subscription_plan = "Starter"  # ✅ DOWNGRADE
        user_tenant.subscription_expiry = datetime.utcnow()
        db.add(user_tenant)

    # -----------------------------
    # COMMIT
    # -----------------------------
    await db.commit()

    return {
        "status": "cancelled",
        "plan": "Starter",
        "message": "Subscription cancelled and downgraded to Starter plan",
        "flutterwave_response": res_data
    }


@router.get("/subscription-status")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db),
    user_tenant=Depends(get_current_user_tenant)
):
    try:
        # ✅ SAFE: NO lazy loading
        tenant_id = user_tenant.tenant_id

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # ----------------------------
        # FETCH BY TENANT
        # ----------------------------
        result = await db.execute(
            select(Subscription).where(Subscription.tenant_id == tenant_id).order_by(Subscription.start_date.desc())
        )
        subscription = result.scalars().first() 

        # ----------------------------
        # DEFAULT
        # ----------------------------
        if not subscription:
            return {
                "plan": "Starter",
                "status": "inactive"
            }

        return {
            "plan": (subscription.plan or "starter").capitalize(),
            "status": subscription.status or "inactive"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail="Subscription service error"
        )