from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path

from models.health import Health
from models.user import UserCreate, UserRead, UserUpdate, ListingGroup, HousingPreference

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Fake in-memory "databases"
# -----------------------------------------------------------------------------
users: Dict[UUID, UserRead] = {}

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Users API",
    description="FastAPI app using Pydantic v2 models for Users Microservice",
    version="0.1.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",                     # Firebase local emulator
        "https://cloud-computing-ui.web.app",        # deployed Firebase site
        "https://cloud-computing-ui.firebaseapp.com" # alt Firebase domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Users API. See /docs for OpenAPI UI."}

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)

# -----------------------------------------------------------------------------
# Users endpoints
# -----------------------------------------------------------------------------

@app.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate) -> UserRead:
    """
    Create a new user. ID is optional in the payload; if not provided, it will
    be generated server-side.
    """
    if payload.id in users:
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    record = UserRead(**payload.model_dump())
    users[record.id] = record
    return record


@app.get("/users", response_model=List[UserRead])
def list_users(
    name: Optional[str] = Query(None, description="Filter by exact name"),
    listing_group: Optional[ListingGroup] = Query(None, description="Filter by listing group"),
    housing_preference: Optional[HousingPreference] = Query(None, description="Filter by housing preference"),
    email: Optional[str] = Query(None, description="Filter by email"),) -> List[UserRead]:
    """
    List users, optionally filtering by any combination of name, listing_group, housing_preference, and email.
    All filters are exact match.
    """
    
    results = list(users.values())
    if name is not None:
        results = [u for u in results if u.name == name]
    if listing_group is not None:
        results = [u for u in results if u.listing_group == listing_group]
    if housing_preference is not None:
        results = [u for u in results if u.housing_preference == housing_preference]
    if email is not None:
        results = [u for u in results if u.email == email]
    return results

@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID) -> UserRead:
    """
    Retrieve a user by their ID.
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]


@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, update: UserUpdate) -> UserRead:
    """
    Apply a partial update to the user.
    Only provided fields are modified; others remain unchanged.
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")

    stored = users[user_id].model_dump()
    stored.update(update.model_dump(exclude_unset=True))
    stored["updated_at"] = datetime.utcnow()

    users[user_id] = UserRead(**stored)
    return users[user_id]


@app.delete("/users/{user_id}")
def delete_user(user_id: UUID):
    """
    Delete and return a confirmation payload
    """
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return {"user_id": str(user_id), "message": "Removed user successfully"}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
