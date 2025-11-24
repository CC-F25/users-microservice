import sys
import os
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path

# Load the .env file from the parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Setup path to find the main app files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_connection import SessionLocal, engine, Base 
from models.user_sql import UserDB
from models.user import HousingPreference, ListingGroup

# Define Dummy Data
DUMMY_USERS = [
    {
        "name": "Ada Kate",
        "email": "ada@gmail.com",
        "phone_number": "+12019460958",
        "housing_preference": HousingPreference.SINGLE_FAMILY_HOME.value,
        "listing_group": ListingGroup.FACEBOOK.value
    },
    {
        "name": "Ben Smith",
        "email": "ben@example.com",
        "phone_number": "+15551234567",
        "housing_preference": HousingPreference.APARTMENT.value,
        "listing_group": ListingGroup.ZILLOW.value
    },
    {
        "name": "Clara Diaz",
        "email": "clara@work.net",
        "phone_number": "+442071112222",
        "housing_preference": "condo",
        "listing_group": "realtor"
    }
]

def seed():
    print("--- Connecting to Database via SQLAlchemy ---")
    db = SessionLocal()
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        print("--- Connection Successful ---")

        count = 0
        for user_data in DUMMY_USERS:
            # Check if user exists to avoid duplicates
            exists = db.query(UserDB).filter(UserDB.email == user_data["email"]).first()
            if not exists:
                new_user = UserDB(**user_data)
                db.add(new_user)
                count += 1
                print(f"queued: {user_data['name']}")
            else:
                print(f"skipped: {user_data['name']} (exists)")
        
        db.commit()
        print(f"--- SUCCESS: Added {count} new users to the REAL 'users' table ---")
        
    except Exception as e:
        print(f"--- ERROR: {e} ---")
    finally:
        db.close()

if __name__ == "__main__":
    seed()