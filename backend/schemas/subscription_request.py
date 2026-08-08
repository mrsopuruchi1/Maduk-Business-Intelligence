from pydantic import BaseModel


class SubscriptionRequest(BaseModel):
    """
    Request schema for subscribing a user to a plan.
    Tenant is resolved automatically from JWT (multi-tenant secure).
    """

    plan: str
    currency: str

    class Config:
        json_schema_extra = {
            "example": {
                "plan": "Professional",
                "currency": "USD"
            }
        }