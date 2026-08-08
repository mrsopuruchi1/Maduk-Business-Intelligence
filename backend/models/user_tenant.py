from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base


class UserTenant(Base):
    __tablename__ = "user_tenant"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    is_owner = Column(Boolean, default=False) 
    role = Column(String, default="Member")

    subscription_plan = Column(String, default="Starter")
    subscription_expiry = Column(DateTime, nullable=True)

    flutterwave_subscription_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="unique_user_tenant"),
    )

    # ✅ CORRECT RELATIONSHIPS
    user = relationship("User", back_populates="user_tenants")
    tenant = relationship("Tenant", back_populates="user_tenants")

    subscriptions = relationship(
        "Subscription",
        back_populates="user_tenant",
        cascade="all, delete-orphan"
    )
    # -----------------------------
    # RELATIONSHIPS (CORRECT)
    # -----------------------------

    # Link to User
    user = relationship("User", back_populates="user_tenants")

    # Link to Tenant
    tenant = relationship("Tenant", back_populates="user_tenants")

    # Link to Subscription (ONE-TO-MANY)
    subscriptions = relationship(
        "Subscription",
        back_populates="user_tenant",
        cascade="all, delete-orphan"
    )