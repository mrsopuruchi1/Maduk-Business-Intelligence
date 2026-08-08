from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database import Base
from sqlalchemy.orm import relationship

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, index=True, nullable=False)  
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    user_tenants = relationship("UserTenant", back_populates="tenant")
    subscriptions = relationship("Subscription", back_populates="tenant")