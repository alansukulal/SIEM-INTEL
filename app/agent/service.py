
from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings
from app.agent.graph import build_investigation_graph
from app.agent.initial_state import create_initial_state
from app.services.conversation_service import (
    get_conversation_history,
    save_message,
)
from app.agent.initial_state import (
    create_initial_state,
    create_follow_up_input,
)
from app.services.investigation_service import get_investigation

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

    # 1. Save the incoming user message.
    save_message(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
        role="user",
        content=alert,
    )

    # 2. Retrieve the conversation history.
    conversation_history = get_conversation_history(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
    )

    # 3. Create the initial graph state with conversation context.
    initial_state = create_initial_state(
        alert=alert,
        siem=siem,
        tenant_id=tenant_id,
        conversation_history=conversation_history,
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

    finding = result.get("finding", "")

    # 4. Save the assistant's response.
    if finding:
        save_message(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            role="assistant",
            content=finding,
        )

    return {
        "investigation_id": investigation_id,
        "thread_id": thread_id,
        "alert": result.get("alert", alert),
        "siem": result.get("siem", siem),
        "plan": result.get("plan", ""),
        "evidence": result.get("evidence", []),
        "finding": finding,
        "investigation_outcome": result.get(
            "investigation_outcome", "unknown"
        ),
    }


def run_follow_up(
    tenant_id: str,
    investigation_id: str,
    alert: str,
) -> dict:

    # 1. Retrieve the existing investigation and thread.
    investigation = get_investigation(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
    )

    if not investigation:
        raise ValueError("Investigation not found.")

    thread_id = str(investigation["thread_id"])

    # 2. Save the new user message.
    save_message(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
        role="user",
        content=alert,
    )

    # 3. Retrieve the complete conversation.
    conversation_history = get_conversation_history(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
    )

    # 4. Prepare a partial state update.
    follow_up_input = create_follow_up_input(
        alert=alert,
        conversation_history=conversation_history,
    )

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    checkpoint_url = get_checkpoint_database_url()

    # 5. Reuse the existing LangGraph checkpoint.
    with PostgresSaver.from_conn_string(
        checkpoint_url
    ) as checkpointer:

        checkpointer.setup()

        graph = build_investigation_graph(
            checkpointer=checkpointer
        )

        result = graph.invoke(
            follow_up_input,
            config=config,
        )

    finding = result.get("finding", "")

    # 6. Save the assistant response.
    if finding:
        save_message(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            role="assistant",
            content=finding,
        )

    return {
        "investigation_id": investigation_id,
        "thread_id": thread_id,
        "alert": alert,
        "siem": result.get("siem", ""),
        "plan": result.get("plan", ""),
        "evidence": result.get("evidence", []),
        "finding": finding,
        "investigation_outcome": result.get(
            "investigation_outcome",
            "unknown",
        ),
    }