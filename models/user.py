from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

class HousingPreference(str, Enum):
    APARTMENT = "apartment"
    SINGLE_FAMILY_HOME = "single_family_home"
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
        json_schema_extra={"example": "amaan@example.com"},
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
                    "email": "amaan@example.com",
                    "phone_number": "+1 (201) 555-0100",
                    "housing_preference": "apartment",
                    "listing_group": "zillow",
                }
            ]
        }
    }
