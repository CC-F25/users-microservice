from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber

class UserBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent User ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    name: str = Field(
        ...,
        description="User's display name.",
        json_schema_extra={"example": "Amaan Sheikh"},
    )
    email: EmailStr = Field(
        ...,
        description="Primary email address.",
        json_schema_extra={"example": "amaan@gmail.com"},
    )
    
    phone_number: Optional[PhoneNumber] = Field(
        default=None,
        description="Primary phone number.",
        json_schema_extra={"example": "+1 (201) 555-0100"},
    )

    bio: Optional[str] = Field(
        default=None,
        description="Short bio or about me.",
        json_schema_extra={"example": "Student at Columbia. Quiet and clean."},
    )
    location: Optional[str] = Field(
        default=None,
        description="Current city/location.",
        json_schema_extra={"example": "New York, NY"},
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Amaan Sheikh",
                    "email": "amaan@gmail.com",
                    "phone_number": "+1 (201) 555-0100",
                    "bio": "CS Grad Student",
                    "location": "New York, NY"
                }
            ]
        }
    )

class UserCreate(UserBase):
    """Creation payload."""
    pass

class UserUpdate(BaseModel):
    """
    Partial update (PATCH) payload. All fields are optional.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[PhoneNumber] = None
    bio: Optional[str] = None
    location: Optional[str] = None

class UserRead(UserBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Amaan Sheikh",
                    "email": "amaan@gmail.com",
                    "phone_number": "+1 (201) 555-0100",
                    "bio": "CS Grad Student",
                    "location": "New York, NY",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    )