from sqlalchemy import Column, String, DateTime
from database_connection import Base
import uuid
from datetime import datetime

class UserDB(Base):
    __tablename__ = "users"

    # columns match the Pydantic model fields
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    bio = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)