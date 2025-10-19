import pymysql
import os
import sys
from dotenv import load_dotenv

load_dotenv()
# Define constants for connection details
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "test_db")


def get_connection(db_name=None):
    """
    Establishes and returns a PyMySQL connection
    """
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
            database=db_name 
        )
        return conn
    except pymysql.Error as e:
        print(f"DATABASE CONNECTION FAILED: {e}")
        sys.exit(1)

def test_database_connection():
    """
    Tests the connection and prints the MySQL version
    """
    print(f"\n--- Testing Connection to {MYSQL_HOST}:{MYSQL_PORT} ---")
    connection = get_connection() 

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"SUCCESS: Connected to MySQL Server version: {version[0]}")
    finally:
        if connection:
            connection.close()

def show_databases():
    """
    Connects and prints all existing databases on the server
    """
    print("\n--- Showing Existing Databases ---")
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES;")
            databases = [db[0] for db in cursor.fetchall()]
            
            print(f"Found {len(databases)} databases:")
            for db in databases:
                print(f" - {db}")
    finally:
        if connection:
            connection.close()

def insert_dummy_data():
    """Connects to the target database, creates the 'users' table, and inserts 5 dummy records only if the table is empty."""
    
    print(f"\n--- Database Initialization: '{MYSQL_DATABASE}.users' ---")
    connection = get_connection(db_name=MYSQL_DATABASE)

    # Define the DDL for the 'users' table (using appropriate VARCHAR lengths)
    CREATE_TABLE_SQL = f"""
    CREATE TABLE IF NOT EXISTS users ( 
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        phone_number VARCHAR(50),
        housing_preference VARCHAR(100),
        listing_group VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Define the 5 dummy records based on the user's provided structure
    DUMMY_RECORDS = [
        ("Ada Kate", "ada@gmail.com", "+1 201 946 0958", "single family home", "facebook"),
        ("Ben Smith", "ben@example.com", "+1 555 123 4567", "apartment", "google_ads"),
        ("Clara Diaz", "clara@work.net", "+44 207 111 2222", "condo", "referral"),
        ("David Lee", "david@web.org", "+61 400 987 654", "townhouse", "linkedin"),
        ("Eva Green", "eva@mail.co", "+33 1 23 45 67 89", "studio", "facebook"),
    ]
    
    # Define the INSERT statement
    INSERT_SQL = """
    INSERT INTO users (name, email, phone_number, housing_preference, listing_group) 
    VALUES (%s, %s, %s, %s, %s);
    """
    
    try:
        with connection.cursor() as cursor:
            # Execute DDL to ensure the 'users' table exists
            cursor.execute(CREATE_TABLE_SQL)
            connection.commit()
            
            # Check the current number of rows to avoid duplication
            cursor.execute("SELECT COUNT(*) FROM users;")
            row_count = cursor.fetchone()[0]

            if row_count == 0:
                # Insert only if the table is empty
                rows_affected = cursor.executemany(INSERT_SQL, DUMMY_RECORDS)
                connection.commit()
                print(f"SUCCESS: Table ensured and {rows_affected} new test users inserted.")
            else:
                #  Skip insertion if data is already present
                print(f"WARNING: Table is not empty ({row_count} records). Skipping dummy data insertion.")
            
    except pymysql.Error as e:
        print(f"FAILURE during DML/DDL: {e}")
    finally:
        if connection:
            connection.close()

def main():
    """
    Database test script to verify connectivity and insert dummy data for microservice testing
    """
    
    # Test basic network and user login connectivity
    test_database_connection()
    
    # Show available databases (optional step)
    show_databases()
    
    # Insert required dummy data for microservice testing
    insert_dummy_data()

if __name__ == "__main__":
    if not all([MYSQL_USER, MYSQL_PASSWORD]):
        print("ERROR: MYSQL_USER and MYSQL_PASSWORD must be defined in the .env file.")
        sys.exit(1)
        
    main()