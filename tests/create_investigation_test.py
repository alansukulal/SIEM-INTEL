
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

try:
    with engine.begin() as connection:

        # Find the tenant
        tenant = connection.execute(
            text("""
                SELECT id
                FROM tenants
                WHERE tenant_key = :tenant_key
            """),
            {"tenant_key": "tenant_a"}
        ).fetchone()

        if not tenant:
            raise ValueError("Tenant not found!")

        # Create an investigation
        investigation = connection.execute(
            text("""
                INSERT INTO investigations
                    (tenant_id, alert, thread_id, status)
                VALUES
                    (:tenant_id, :alert, :thread_id, :status)
                RETURNING id, alert, thread_id
            """),
            {
                "tenant_id": tenant.id,
                "alert": "Sentinel ingestion spike detected",
                "thread_id": "thread-002",
                "status": "running"
            }
        ).fetchone()

        print("Investigation created successfully!")
        print("Investigation ID:", investigation.id)
        print("Alert:", investigation.alert)
        print("Thread ID:", investigation.thread_id)

except Exception as error:
    print("Error:", error)
