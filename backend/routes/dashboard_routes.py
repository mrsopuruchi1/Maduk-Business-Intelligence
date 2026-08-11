from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.utils.auth import get_current_user_tenant

router = APIRouter(prefix="", tags=["Dashboard"])


@router.get("/dashboard", name="get_dashboard")
async def dashboard(
    user_tenant=Depends(get_current_user_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Return tenant-scoped dashboard data for the authenticated user."""
    return {
        "tenant_id": user_tenant.tenant_id,
        "plan": user_tenant.subscription_plan or "Starter",
        "user_role": user_tenant.role or "Member",
        "dashboard": {
            "total_clients": 0,
            "active_campaigns": 0,
            "monthly_revenue": 0,
        },
        "source": "live",
    }
