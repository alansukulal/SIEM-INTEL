
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), version()")
        )

        database, version = result.fetchone()

        print("Connected successfully!")
        print("Database:", database)
        print("PostgreSQL:", version)

except Exception as error:
    print("Database connection failed:", error)
