from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import Pydantic Models
from models.health import Health
from models.user import UserCreate, UserRead, UserUpdate, ListingGroup, HousingPreference

# Import Database connection and SQL Model
from database_connection import Base, engine, get_db
from models.user_sql import UserDB

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Database setup
# -----------------------------------------------------------------------------

# This creates the table automatically if it doesn't exist
Base.metadata.create_all(bind=engine)

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
    return {
        "message": "Welcome to the Users API.",
        "documentation": "/docs",
        "endpoints": {
            "list_users": "/users", 
            "create_user": "/users",
            "health": "/health",
            "test_db": "/test-db"
        }
    }

# -----------------------------------------------------------------------------
# test-db endpoint
# -----------------------------------------------------------------------------

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # run a simple query to test the connection
        result = db.execute(text("SELECT 1")).fetchone()
        return {"status": "success", "result": result[0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user. ID is optional in the payload; if not provided, it will
    be generated server-side.
    """
    # check if ID already exists
    if db.query(UserDB).filter(UserDB.id == str(payload.id)).first():
        raise HTTPException(status_code=400, detail="User with this ID already exists")

    # check if Email already exists
    if db.query(UserDB).filter(UserDB.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # create SQL Model using the payload's ID
    new_user = UserDB(
        id=str(payload.id),
        name=payload.name,
        email=payload.email,
        phone_number=str(payload.phone_number).replace("tel:", ""),
        housing_preference=payload.housing_preference.value,
        listing_group=payload.listing_group.value
    )
    
    # add and commit to DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[UserRead])
def list_users(
    offset: int = 0, 
    limit: int = 10, 
    name: Optional[str] = Query(None, description="Filter by exact name"),
    listing_group: Optional[ListingGroup] = Query(None, description="Filter by listing group"),
    housing_preference: Optional[HousingPreference] = Query(None, description="Filter by housing preference"),
    email: Optional[str] = Query(None, description="Filter by email"),
    db: Session = Depends(get_db)
    ) -> List[UserRead]:
    """
    List all users, optionally filtering by any combination of name, listing_group, housing_preference, and email.
    All filters are exact match.
    """
    query = db.query(UserDB)
    
    # Filter 1: Name
    if name:
        query = query.filter(UserDB.name == name)
        
    # Filter 2: Email
    if email:
        query = query.filter(UserDB.email == email)
        
    # Filter 3: Listing Group (Extract string value from Enum)
    if listing_group:
        query = query.filter(UserDB.listing_group == listing_group.value)
        
    # Filter 4: Housing Preference (Extract string value from Enum)
    if housing_preference:
        query = query.filter(UserDB.housing_preference == housing_preference.value)
        
    # Apply Pagination (Limit/Offset)
    return query.offset(offset).limit(limit).all()

@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve a user by their ID.
    """
    user = db.query(UserDB).filter(UserDB.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, update: UserUpdate, db: Session = Depends(get_db)):
    """
    Apply a partial update to the user.
    Only provided fields are modified; others remain unchanged.
    """
    user = db.query(UserDB).filter(UserDB.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # update fields
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(value, 'value'):
            value = value.value

        if key == "phone_number":
            value = str(value).replace("tel:", "")

        setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Delete and return a confirmation payload
    """
    user = db.query(UserDB).filter(UserDB.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
