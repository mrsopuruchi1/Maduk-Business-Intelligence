from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional 

from backend.database import Base


class Subscription(Base):
    """
    Subscription table for Maduk Business Intelligence AI SaaS platform
    Supports multi-tenant architecture (user + tenant context)
    """

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # -----------------------------
    # RELATIONSHIPS
    # -----------------------------

    # Link to User
    user_email = Column(String) 
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Link to Tenant
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    # Link to UserTenant (IMPORTANT)
    user_tenant_id = Column(Integer, ForeignKey("user_tenant.id"), nullable=False)

    # -----------------------------
    # SUBSCRIPTION DETAILS
    # -----------------------------

    # Plan name (Starter, Professional, Agency, Enterprise)
    plan = Column(String, default="Starter")

    # Payment status (active, inactive, cancelled)
    status = Column(String, default="inactive")

    # Flutterwave subscription ID
    flutterwave_subscription_id = Column(String, nullable=True)

    # Flutterwave transaction reference (for webhook verification)
    tx_ref = Column(String, unique=True, index=True) 

    # Currency used
    currency = Column(String, default="USD")

    # Amount paid
    amount = Column(Integer, nullable=True)

    # -----------------------------
    # TIMESTAMPS
    # -----------------------------

    # Subscription start date
    start_date = Column(DateTime, default=datetime.utcnow)

    # Subscription expiry date
    expiry_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    pass_due_start: Optional[datetime] = Column(DateTime, nullable=True) 

    # -----------------------------
    # ORM RELATIONSHIPS
    # -----------------------------

    user = relationship("User")

    tenant = relationship("Tenant")

    user_tenant = relationship("UserTenant", back_populates="subscriptions")