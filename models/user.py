from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

class HousingPreference(str, Enum):
    APARTMENT = "apartment"
    SINGLE_FAMILY_HOME = "single family home"
    TOWNHOUSE = "townhouse"
    CONDO = "condo"
    STUDIO = "studio"
    OTHER = "other"

class ListingGroup(str, Enum):
    FACEBOOK = "facebook"
    ZILLOW = "zillow"
    CRAIGSLIST = "craigslist"
    REALTOR = "realtor"
    OTHER = "other"

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
    phone_number: PhoneNumber = Field(
        ...,
        description="Primary phone number (lenient validation).",
        json_schema_extra={"example": "+1 (201) 555-0100"},
    )
    housing_preference: HousingPreference = Field(
        ...,
        description="Preferred housing type.",
        json_schema_extra={"example": HousingPreference.APARTMENT.value},
    )
    listing_group: ListingGroup = Field(
        ...,
        description="Listing source/segment.",
        json_schema_extra={"example": ListingGroup.ZILLOW.value},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Amaan Sheikh",
                    "email": "amaan@gmail.com",
                    "phone_number": "+1 (201) 555-0100",
                    "housing_preference": "apartment",
                    "listing_group": "zillow",
                }
            ]
        }
    }

class UserCreate(UserBase):
    """Creation payload; ID defaults server-side but can be supplied."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Ada Kate",
                    "email": "ada@gmail.com",
                    "phone_number": "+1 201 946 0958",
                    "housing_preference": "single family home",
                    "listing_group": "facebook",
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    """
    Full replace (PUT) payload; ID comes from path.
    """
    name: str = Field(..., description="User's display name.")
    email: EmailStr = Field(..., description="Primary email address.")
    phone_number: PhoneNumber = Field(..., description="Primary phone number.")
    housing_preference: HousingPreference = Field(..., description="Preferred housing type.")
    listing_group: ListingGroup = Field(..., description="Listing source/segment.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Ada Lovelace",
                    "email": "ada@gmail.com",
                    "phone_number": "+44 20 7000 0000",
                    "housing_preference": "townhouse",
                    "listing_group": "realtor",
                }
            ]
        }
    }

class UserRead(UserBase):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Amaan Sheikh",
                    "email": "amaan@gmail.com",
                    "phone_number": "+1 (201) 555-0100",
                    "housing_preference": "apartment",
                    "listing_group": "zillow",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }