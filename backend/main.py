# backend/main.py

import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import aioredis

from backend.database import Base, init_db
from backend.services.auth import get_current_user
from backend.routes import subscription_routes
from backend.routes import auth_routes
from backend.routes.flutterwave_webhook import router as flutterwave_webhook_router
from backend.routes import tenant_routes, dashboard_routes
from backend.routes import data_intelligence_pipeline_route 
from backend.routes import ai_prediction_pipeline_route 
from backend.routes import ai_recommendation_pipeline_route 



# ----------------------------
# ENVIRONMENT VARIABLES
# ----------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ----------------------------
# APP INITIALIZATION
# ----------------------------
app = FastAPI(title="Maduk Business Intelligence")

# ----------------------------
# ROUTES
# ----------------------------
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(subscription_routes.router, tags=["Subscription"])
app.include_router(flutterwave_webhook_router)
app.include_router(tenant_routes.router)
app.include_router(dashboard_routes.router, tags=["Dashboard"])
app.include_router(data_intelligence_pipeline_route.router)
app.include_router(ai_prediction_pipeline_route.router)
app.include_router(ai_recommendation_pipeline_route.router)


# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# DATABASE SETUP
# ----------------------------
engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# ----------------------------
# REDIS (SAFE MODE)
# ----------------------------
try:
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
except:
    redis = None

# ----------------------------
# TENANT AUTH (UPDATED)
# ----------------------------
async def get_current_tenant(
    authorization: Optional[str] = Header(None)
):
    """
    Extract tenant_id from JWT token.
    Required for tenant-scoped endpoints like dashboard, billing, subscription.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        tenant_id = payload.get("tenant_id")

        if tenant_id is None:
            raise HTTPException(status_code=401, detail="Tenant not found in token")

        return tenant_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------------------
# DASHBOARD (TENANT-AWARE)
# ----------------------------
@app.get("/dashboard")
async def dashboard(
    tenant_id: int = Depends(get_current_tenant),
    user_email: str = Depends(get_current_user)
):
    """
    Tenant-specific dashboard.
    """

    cache_key = f"dashboard:{tenant_id}"

    # Try Redis
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return {
                    "tenant_id": tenant_id,
                    "user": user_email,
                    "dashboard": cached
                }
        except:
            pass

    # Simulated tenant-specific data
    data = {
        "tenant_id": tenant_id,
        "total_clients": 120,
        "active_campaigns": 25,
        "monthly_revenue": 50000
    }

    # Cache it
    if redis:
        try:
            await redis.set(cache_key, str(data), ex=300)
        except:
            pass

    return {
        "tenant_id": tenant_id,
        "user": user_email,
        "dashboard": data
    }

# ----------------------------
# CLIENT DATA (TENANT-AWARE)
# ----------------------------
@app.get("/clients")
async def clients(
    tenant_id: int = Depends(get_current_tenant),
    user_email: str = Depends(get_current_user)
):
    return {
        "tenant_id": tenant_id,
        "user": user_email,
        "clients": [
            {"name": "Client A", "revenue": 5000},
            {"name": "Client B", "revenue": 8000},
        ]
    }

# ----------------------------
# REPORTS (TENANT-AWARE)
# ----------------------------
@app.get("/reports")
async def reports(
    tenant_id: int = Depends(get_current_tenant),
    user_email: str = Depends(get_current_user)
):
    return {
        "tenant_id": tenant_id,
        "user": user_email,
        "reports": ["Report1.pdf", "Report2.pdf"]
    }

# ----------------------------
# AI BUSINESS ADVICE (TENANT-AWARE)
# ----------------------------
@app.get("/ai-advice")
async def ai_advice(
    query: str = "",
    tenant_id: int = Depends(get_current_tenant),
    user_email: str = Depends(get_current_user)
):
    return {
        "tenant_id": tenant_id,
        "user": user_email,
        "query": query,
        "advice": [
            "Increase ad spend on campaigns with high ROI.",
            "Offer premium packages to high-value clients to reduce churn."
        ]
    }

# ----------------------------
# HEALTH CHECK
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Maduk Business Intelligence Backend Running"}

# ----------------------------
# STARTUP
# ----------------------------
@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/payment-success")
async def payment_success(status: str = None, tx_ref: str = None, transaction_id: int = None):
    return {"message": "Payment successful", "status": status, "tx_ref": tx_ref, "transaction_id": transaction_id} 