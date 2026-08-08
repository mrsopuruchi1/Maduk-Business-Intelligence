from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta 

from backend.database import get_db
from backend.models.subscription import Subscription
from backend.services.plan_access import activate_subscription

router = APIRouter(
    prefix="/flutterwave",
    tags=["Flutterwave Webhook"]
)

# Load Flutterwave secret hash from .env
load_dotenv()
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH")


@router.post("/webhook")
async def flutterwave_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    subscription = None  # Initialize early to prevent UnboundLocalError

    try:
        # -----------------------------
        # VERIFY SIGNATURE
        # -----------------------------
        signature = request.headers.get("verif-hash")
        if not signature or signature != FLUTTERWAVE_SECRET_HASH:
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # -----------------------------
        # PARSE PAYLOAD
        # -----------------------------
        payload = await request.json()
        print("Webhook received:", payload)

        event = payload.get("event")
        if event != "charge.completed":
            print("Ignored event:", event)
            return {"status": "ignored"}

        data = payload.get("data", {})
        transaction_id = data.get("id")
        tx_ref = data.get("tx_ref")
        status = data.get("status")

        if not transaction_id or not tx_ref:
            raise HTTPException(status_code=400, detail="Invalid payload")

        print("Transaction ID:", transaction_id)
        print("TX_REF:", tx_ref)
        print("Status:", status)

        # -----------------------------
        # FETCH SUBSCRIPTION BY TX_REF
        # -----------------------------
        result = await db.execute(
            select(Subscription).where(Subscription.tx_ref == tx_ref).order_by(Subscription.id.desc()) 
        )
        subscription = result.scalars().first() 

        if subscription is None:
            print("Ignored: No subscription found for tx_ref:", tx_ref)
            return {"status": "ignored"} 
        
        if subscription.status == "active":
            print("Subscription already active, skipping") 
            return {"status": "already_processed"} 

        # -----------------------------
        # PROCESS PAYMENT
        # -----------------------------
        now = datetime.utcnow() 

        if status and status.lower() == "successful":

            flutterwave_sub_id = data.get("subscription_id") or data.get("id") 

            if flutterwave_sub_id:
                subscription.flutterwave_subscription_id = flutterwave_sub_id 
                 

            print("flutterwave Subscription ID:", flutterwave_sub_id) 
            print(f"🚀 Activating subscription {subscription.id} for tenant {subscription.tenant_id}")

            # Activate subscription via plan_access service
            await activate_subscription(
                db=db,
                user_tenant_id=subscription.user_tenant_id,
                plan=subscription.plan,
                flutterwave_tx_id=flutterwave_sub_id 
            )

            # Update subscription record
            subscription.past_due_start = None 
            subscription.status = "active"
            subscription.flutterwave_subscription_id = transaction_id

        else:
            print(f"❌ Payment failed for subscription {subscription.id}")

            if subscription.status != "pass_due":
                subscription.status = "pass_due"
                Subscription.pass_due_start = now 
            else:
                if subscription.pass_due_start and (now - subscription.pass_due_start) >= timedelta(days=5):
                    print(f"Subscription {subscription.id} exceeded grace period. Downgrading to Starter plan.") 
                    subscription.plan = "Starter"
                    subscription.status = "active"
                    subscription.pass_due_star = None 
            subscription.flutterwave_subscription_id = transaction_id  
             
            

        db.add(subscription)
        await db.commit()

        print(f"✅ Subscription {subscription.id} status updated to {subscription.status}")
        return {"status": subscription.status}

    except HTTPException:
        raise  # Preserve original HTTP errors

    except Exception as e:
        print("🔥 Webhook Error:", str(e))
        if subscription:
            print("Last known subscription ID:", subscription.id)
        raise HTTPException(status_code=500, detail="Internal server error")