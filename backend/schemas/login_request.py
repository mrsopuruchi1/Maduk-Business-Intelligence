# backend/schemas/login_request.py

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Schema for user login.
    Multi-tenant aware: login authenticates user email and password.
    """

    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=6, description="User password")

    class Config:
        schema_extra = {
            "example": {
                "email": "alice@company.com",
                "password": "StrongPass123"
            }
        }