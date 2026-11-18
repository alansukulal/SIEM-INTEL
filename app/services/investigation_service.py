
from uuid import uuid4

from sqlalchemy import text

from app.config import settings
from sqlalchemy import create_engine


engine = create_engine(settings.database_url)


def create_investigation(
    tenant_id: str,
    alert: str,
) -> dict:
    thread_id = str(uuid4())

    with engine.begin() as connection:
        investigation = connection.execute(
            text("""
                INSERT INTO investigations (
                    tenant_id,
                    alert,
                    status,
                    thread_id
                )
                VALUES (
                    :tenant_id,
                    :alert,
                    :status,
                    :thread_id
                )
                RETURNING id, tenant_id, alert, status, thread_id
            """),
            {
                "tenant_id": tenant_id,
                "alert": alert,
                "status": "running",
                "thread_id": thread_id,
            },
        ).mappings().one()

    return dict(investigation)
