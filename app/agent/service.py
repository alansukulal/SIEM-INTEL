
from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings
from app.agent.graph import build_investigation_graph
from app.agent.initial_state import create_initial_state


def get_checkpoint_database_url() -> str:
    """Convert SQLAlchemy's URL to a native Psycopg URL."""
    return settings.database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )


def run_investigation(
    tenant_id: str,
    investigation_id: str,
    thread_id: str,
    alert: str,
    siem: str,
) -> dict:

    initial_state = create_initial_state(
        alert=alert,
        siem=siem,
        tenant_id=tenant_id,
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    checkpoint_url = get_checkpoint_database_url()

    with PostgresSaver.from_conn_string(
        checkpoint_url
    ) as checkpointer:

        checkpointer.setup()

        graph = build_investigation_graph(
            checkpointer=checkpointer
        )

        result = graph.invoke(
            initial_state,
            config=config,
        )

    return {
        "investigation_id": investigation_id,
        "thread_id": thread_id,
        "alert": result.get("alert", alert),
        "siem": result.get("siem", siem),
        "plan": result.get("plan", ""),
        "evidence": result.get("evidence", []),
        "finding": result.get("finding", ""),
        "investigation_outcome": result.get(
            "investigation_outcome", "unknown"
        ),
    }
