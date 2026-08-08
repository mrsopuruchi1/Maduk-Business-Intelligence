# backend/schemas/signup_request.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    """
    Schema for signing up a user.
    Multi-tenant aware: optionally allows creating a tenant on signup.
    """

    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=6, description="User password")
    
    # Optional tenant creation on signup
    tenant_name: Optional[str] = Field(
        None, 
        description="Name of the tenant to create on signup (optional)"
    )

    class Config:
        schema_extra = {
            "example": {
                "email": "alice@company.com",
                "password": "StrongPass123",
                "tenant_name": "Company ABC"  # optional
            }
        }