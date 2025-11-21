from sqlalchemy import Column, String, DateTime
from database import Base
import uuid
from datetime import datetime

class UserDB(Base):
    __tablename__ = "users"

    # columns match the Pydantic model fields
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20))
    housing_preference = Column(String(50)) 
    listing_group = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)