
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

def get_investigation(
    tenant_id: str,
    investigation_id: str,
) -> dict | None:

    with engine.connect() as connection:
        investigation = connection.execute(
            text("""
                SELECT
                    id,
                    tenant_id,
                    alert,
                    status,
                    thread_id
                FROM investigations
                WHERE tenant_id = :tenant_id
                  AND id = :investigation_id
            """),
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
            },
        ).mappings().one_or_none()

    return dict(investigation) if investigation else None

def update_investigation_status(
    tenant_id: str,
    investigation_id: str,
    status: str,
) -> bool:

    if status not in ("running", "completed", "failed"):
        raise ValueError("Invalid investigation status")

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE investigations
                SET status = :status
                WHERE tenant_id = :tenant_id
                  AND id = :investigation_id
            """),
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
                "status": status,
            },
        )

    return result.rowcount == 1