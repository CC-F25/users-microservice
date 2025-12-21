from __future__ import annotations

import os
import socket
from datetime import datetime
import json
import time
import uuid
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

# Google & Auth
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.cloud import pubsub_v1

# Models
from models.health import Health
from models.user import UserCreate, UserRead, UserUpdate
from models.user_sql import UserDB
from database_connection import Base, engine, get_db

load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = "HS256"
JWT_EXP_SECONDS = 3600
GOOGLE_CLIENT_ID = get_required_env("GOOGLE_CLIENT_ID")
PUBSUB_PROJECT = os.getenv("GCP_PROJECT_ID")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC")


def generate_token(user_id: str, email: str, expires_in: int, typ: str):
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + expires_in,
        "typ": typ,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def generate_jwt(user_id: str, email: str):
    return generate_token(user_id, email, JWT_EXP_SECONDS, "access")

def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if payload.get("typ") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


publisher = None
topic_path = None
if PUBSUB_PROJECT and PUBSUB_TOPIC:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PUBSUB_PROJECT, PUBSUB_TOPIC)

def publish_user_event(event_type: str, payload: dict):
    """
    Publishes a JSON event to Google Pub/Sub.
    Works locally (if GOOGLE_APPLICATION_CREDENTIALS is set) or on Cloud Run.
    """
    if not publisher or not topic_path:
        print("Pub/Sub publisher not configured; skipping event publish.")
        return

    message = json.dumps({
        "event_type": event_type,
        "timestamp": int(time.time()),
        "payload": payload
    }).encode("utf-8")

    future = publisher.publish(topic_path, message)
    print(f"Published event {event_type}, message ID: {future.result()}")


port = int(os.environ.get("PORT", 8080))

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
# google auth endpoint
# -----------------------------------------------------------------------------
    
@app.post("/auth/google")
def google_login(google_token: str, db: Session = Depends(get_db)):
    """
    The MASTER Endpoint.
    1. Verifies Google Token.
    2. Checks if User exists.
    3. IF NEW: Creates 'Skeleton User' (Name/Email) & Publishes Event.
    4. IF EXISTING: Just logs them in.
    5. Returns JWT.
    """
    # Verify Google Token
    try:
        google_info = id_token.verify_oauth2_token(
            google_token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = google_info["email"]
    name = google_info.get("name", "Unknown User")
    
    # Check if user exists
    user_db = db.query(UserDB).filter(UserDB.email == email).first()

    # IF NEW USER: Create & Publish
    if not user_db:
        print(f"New user detected: {email}")
        new_user_id = str(uuid.uuid4())
        
        # Create Skeleton User (No phone, no bio yet)
        user_db = UserDB(
            id=new_user_id,
            email=email,
            name=name,
            phone_number=None, 
            bio=None,
            location=None
        )
        db.add(user_db)
        db.commit()
        db.refresh(user_db)

        # Publish "User Created" Event
        try:
            publish_user_event("USER_CREATED", {
                "id": new_user_id, 
                "email": email, 
            })
            print(f"Published USER_CREATED event for {email}")
        except Exception as e:
            print(f"Warning: Failed to publish event: {e}")

    # Generate JWT
    access_token = generate_jwt(user_db.id, user_db.email)
    
    # Return User Data (Frontend checks if phone_number is null to show profile form)
    return {
        "access_jwt": access_token, 
        "user": {
            "id": user_db.id, 
            "name": user_db.name, 
            "email": user_db.email,
            "phone_number": user_db.phone_number,
            "bio": user_db.bio,
            "location": user_db.location
        }
    }

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

@app.get("/users", response_model=List[UserRead])
def list_users(
    offset: int = 0, 
    limit: int = 10, 
    name: Optional[str] = Query(None, description="Filter by exact name"),
    email: Optional[str] = Query(None, description="Filter by email"),
    db: Session = Depends(get_db),
    ) -> List[UserRead]:
    """
    List users, optionally filtering by name or email.
    """
    query = db.query(UserDB)
    
    if name:
        query = query.filter(UserDB.name == name)
    if email:
        query = query.filter(UserDB.email == email)
    
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
def update_user(
    user_id: str, 
    payload: UserUpdate, 
    db: Session = Depends(get_db), 
    auth: Dict = Depends(require_auth)):
    """
    Update profile (Phone, Bio, Location)
    """
    # Security Check
    if auth["sub"] != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    # Get User
    user_db = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Update Fields
    if payload.name:
        user_db.name = payload.name
    
    # Handle Pydantic PhoneNumber object to String
    if payload.phone_number:
        user_db.phone_number = str(payload.phone_number)
        
    # New Fields
    if payload.bio:
        user_db.bio = payload.bio
    if payload.location:
        user_db.location = payload.location
    
    user_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_db)

    # Publish "User Updated" Event
    publish_user_event("USER_UPDATED", {"id": user_db.id})

    return user_db


@app.delete("/users/{user_id}")
def delete_user(user_id: UUID, db: Session = Depends(get_db), auth: Dict = Depends(require_auth)):
    """
    Delete and return a confirmation payload
    """
    if str(user_id) != auth["sub"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    user = db.query(UserDB).filter(UserDB.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()

    # pub/sub
    publish_user_event("USER_DELETED", {"id": str(user_id)})


    return {"message": "User deleted successfully"}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
