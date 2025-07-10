import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

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

    db_name = os.getenv("DB_NAME")

    # Drop the database if it exists to ensure a clean start
    print(f"Attempting to drop database '{db_name}' if it exists...")
    # Using WITH (FORCE) to terminate any active connections
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)")
    print(f"Database '{db_name}' dropped or did not exist.")

    # Create the database
    print(f"Creating database '{db_name}'...")
    cursor.execute(f"CREATE DATABASE {db_name}")
    print(f"Database '{db_name}' created successfully.")

except psycopg2.OperationalError as e:
    print(f"Error: Could not connect to PostgreSQL.")
    print(f"Please ensure PostgreSQL is running and the connection details in .env are correct.")
    print(f"Details: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    if 'conn' in locals() and conn is not None:
        conn.close()