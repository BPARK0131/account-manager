import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from app.database import engine, Base
# Import all models to ensure they are registered with Base
from app import models

# Load environment variables from .env file
load_dotenv()

def recreate_database():
    """
    Drops the existing database (if it exists) and creates a new one.
    """
    db_name = os.getenv("DB_NAME")
    if not db_name:
        print("Error: DB_NAME not found in .env file.")
        return

    try:
        # Connect to the default 'postgres' database to manage our target database
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Drop the database if it exists to ensure a clean start
        print(f"Attempting to drop database '{db_name}' if it exists...")
        # Using WITH (FORCE) is a PostgreSQL-specific feature to terminate active connections
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)")
        print(f"Database '{db_name}' dropped successfully or did not exist.")

        # Create the database
        print(f"Creating database '{db_name}'...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database '{db_name}' created successfully.")

    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to PostgreSQL server.")
        print(f"Please ensure PostgreSQL is running and connection details in .env are correct.")
        print(f"Details: {e}")
        # Exit if we can't connect, as further steps will fail
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during database recreation: {e}")
        exit(1)
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

def create_tables():
    """
    Creates all tables in the database based on the SQLAlchemy models.
    """
    try:
        print("Creating tables...")
        # The engine is configured for the specific database (e.g., 'account_manager_db')
        # Base.metadata.create_all() will issue CREATE TABLE statements for all models
        # that inherit from Base.
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"An error occurred during table creation: {e}")
        print("Please check your database connection and model definitions.")
        exit(1)

if __name__ == "__main__":
    print("--- Starting Database Setup ---")
    recreate_database()
    create_tables()
    print("--- Database Setup Complete ---")
