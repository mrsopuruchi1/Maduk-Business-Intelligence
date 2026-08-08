from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import User


async def check_subscription_access(email: str, required_feature: str, db: AsyncSession):
    """
    Ensures user subscription allows access to a feature.
    """

    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Starter plan access
    starter_features = [
        "data_upload",
        "analysis",
        "visualisation",
        "conclusion"
    ]

    professional_features = starter_features + [
        "campaign_prediction",
        "churn_prediction",
        "revenue_forecast",
        "pdf_reports"
    ]

    agency_features = professional_features + [
        "budget_optimizer",
        "anomaly_detection",
        "growth_strategy",
        "ai_chatbot"
    ]

    enterprise_features = agency_features + [
        "multi_client",
        "api_access",
        "autonomous_ai_consultant"
    ]

    plan_features = {
        "starter": starter_features,
        "professional": professional_features,
        "agency": agency_features,
        "enterprise": enterprise_features
    }

    user_plan = user.plan.lower()

    if required_feature not in plan_features.get(user_plan, []):
        raise HTTPException(
            status_code=403,
            detail="Upgrade your subscription to access this feature"
        )

    # Check expiry
    if user.subscription_expiry and user.subscription_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail="Subscription expired"
        )

    return True