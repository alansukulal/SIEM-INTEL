
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Use the existing investigation
with engine.connect() as connection:
    investigation = connection.execute(
        text("""
            SELECT id, tenant_id
            FROM investigations
            LIMIT 1
        """)
    ).mappings().first()

if not investigation:
    raise RuntimeError("No investigation found. Create one first.")

tenant_id = investigation["tenant_id"]
investigation_id = investigation["id"]

# Insert conversation messages
with engine.begin() as connection:
    connection.execute(
        text("""
            INSERT INTO investigation_messages
                (tenant_id, investigation_id, role, content)
            VALUES
                (:tenant_id, :investigation_id, :role, :content)
        """),
        [
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
                "role": "user",
                "content": "Why has Sentinel ingestion stopped?"
            },
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
                "role": "assistant",
                "content": "The ingestion failure may be related to an expired authentication token."
            }
        ]
    )

print("Messages inserted successfully!")

# Retrieve conversation history
with engine.connect() as connection:
    messages = connection.execute(
        text("""
            SELECT role, content, created_at
            FROM investigation_messages
            WHERE tenant_id = :tenant_id
              AND investigation_id = :investigation_id
            ORDER BY created_at, id
        """),
        {
            "tenant_id": tenant_id,
            "investigation_id": investigation_id
        }
    ).mappings().all()

print("\nConversation History:")
for message in messages:
    print(f"{message['role']}: {message['content']}")
