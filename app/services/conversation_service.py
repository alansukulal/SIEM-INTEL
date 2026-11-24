
from sqlalchemy import text

from app.services.investigation_service import engine


def get_conversation_history(
    tenant_id: str,
    investigation_id: str,
) -> list[dict[str, str]]:

    with engine.connect() as connection:
        messages = connection.execute(
            text("""
                SELECT role, content
                FROM investigation_messages
                WHERE tenant_id = :tenant_id
                  AND investigation_id = :investigation_id
                ORDER BY created_at, id
            """),
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
            },
        ).mappings().all()

    return [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
    ]


def save_message(
    tenant_id: str,
    investigation_id: str,
    role: str,
    content: str,
) -> None:

    if role not in ("user", "assistant", "system", "tool"):
        raise ValueError("Invalid message role")

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO investigation_messages
                    (tenant_id, investigation_id, role, content)
                VALUES
                    (:tenant_id, :investigation_id, :role, :content)
            """),
            {
                "tenant_id": tenant_id,
                "investigation_id": investigation_id,
                "role": role,
                "content": content,
            },
        )
