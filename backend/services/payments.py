# backend/services/payments.py

import os
import httpx
from datetime import datetime

from backend.services.plan_access import activate_subscription

FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
FLUTTERWAVE_BASE_URL = "https://api.flutterwave.com/v3"

# ----------------------------------
# PLAN PRICING
# ----------------------------------

PLAN_PRICES = {
    "Starter": 0,
    "Professional": 30,
    "Agency": 50,
    "Enterprise": 100
}

USD_TO_NGN = 800

PLAN_IDS = {"Professional": 231204, "Agency": 231205, "Enterprise": 231206} 

# ----------------------------------
# CREATE PAYMENT LINK (MULTI-TENANT)
# ----------------------------------

async def create_payment_plan(name: str, amount: int):
    url = "https://api.flutterwave.com/v3/payment-plans"

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}"
    }

    payload = {
        "amount": amount,
        "name": name,
        "interval": "monthly"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()



async def create_flutterwave_subscription(
    email: str,
    plan: str,
    currency: str,
    tenant_id: int,
    user_tenant_id: int = None,
    amount_multiplier: int = 1
):
    """
    Create Flutterwave payment link for subscription.
    """

    usd_amount = PLAN_PRICES.get(plan, 0)

    # Apply multiplier (backward compatibility)
    usd_amount = usd_amount * amount_multiplier

    # Currency conversion
    if currency == "NGN":
        amount = usd_amount * USD_TO_NGN
    else:
        amount = usd_amount
        currency = "USD"

    tx_ref = f"tx-{email}-{tenant_id}-{plan}-{int(datetime.utcnow().timestamp())}"

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": currency,
        "redirect_url": "http://localhost:8000/payment-success",
        "payment_plan": PLAN_IDS[plan],
        "customer": {
            "email": email
        },
        "meta": {
            "plan": plan,
            "tenant_id": tenant_id,
            "user_email": email,
            "user_tenant_id": user_tenant_id
        },
        "customizations": {
            "title": "Maduk Business Intelligence",
            "description": f"{plan} Subscription Plan"
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FLUTTERWAVE_BASE_URL}/payments",
            json=payload,
            headers=headers
        )

    if resp.status_code != 200:
        raise Exception(f"Flutterwave Error: {resp.text}")

    result = resp.json()

    return {
        "payment_link": result["data"]["link"],
        "tx_ref": tx_ref
    }


# ----------------------------------
# VERIFY PAYMENT + ACTIVATE PLAN
# ----------------------------------

async def verify_flutterwave_transaction(transaction_id: str, db):
    """
    Verify Flutterwave transaction and activate subscription.
    Integrated with plan_access service.
    """

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{FLUTTERWAVE_BASE_URL}/transactions/{transaction_id}/verify",
            headers=headers
        )

    if resp.status_code != 200:
        raise Exception(f"Verification failed: {resp.text}")

    data = resp.json()["data"]

    status = data["status"]

    # Extract metadata (VERY IMPORTANT)
    meta = data.get("meta", {})

    plan = meta.get("plan", "Professional")
    tenant_id = meta.get("tenant_id")
    user_email = meta.get("user_email")

    if not tenant_id or not user_email:
        raise Exception("Missing tenant_id or user_email in metadata")

    # ----------------------------------
    # SUCCESS → ACTIVATE SUBSCRIPTION
    # ----------------------------------

    if status == "successful":

        await activate_subscription(
            db=db,
            user_tenant_id=subscription.user_tenant_id,
            plan=subscription.plan,
            flutterwave_tx_id=transaction_id 
        )

        return {
            "status": "success",
            "message": "Subscription activated",
            "plan": plan,
            "tenant_id": tenant_id
        }

    return {
        "status": "failed",
        "message": "Payment not successful"
    }


print("FLW_SECRET_KEY:", FLUTTERWAVE_SECRET_KEY)