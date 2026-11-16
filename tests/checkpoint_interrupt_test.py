
import os
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import interrupt

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
    1
)


# 1. Define investigation state
class InvestigationState(TypedDict):
    alert: str
    plan: str
    query: str
    approval: str
    finding: str


# 2. Define graph nodes
def planner(state):
    print("Planner executing...")

    return {
        "plan": f"Investigate alert: {state['alert']}"
    }


def kql_generator(state):
    print("KQL Generator executing...")

    return {
        "query": "Heartbeat | summarize count() by Computer"
    }


def approval_node(state):
    print("\nWaiting for analyst approval...")

    decision = interrupt({
        "message": "Approve this KQL query?",
        "query": state["query"]
    })

    return {"approval": decision}


def investigator(state):
    print("Investigator executing...")

    return {
        "finding": (
            f"Investigation completed for {state['alert']}. "
            f"Approval: {state['approval']}"
        )
    }


# 3. Build graph
builder = StateGraph(InvestigationState)

builder.add_node("planner", planner)
builder.add_node("kql_generator", kql_generator)
builder.add_node("approval", approval_node)
builder.add_node("investigator", investigator)

builder.add_edge(START, "planner")
builder.add_edge("planner", "kql_generator")
builder.add_edge("kql_generator", "approval")
builder.add_edge("approval", "investigator")
builder.add_edge("investigator", END)


# 4. Configure PostgreSQL checkpointer
with PostgresSaver.from_conn_string(
    CHECKPOINT_DATABASE_URL
) as checkpointer:

    checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "siem-interrupt-001"
        }
    }

    # 5. Start investigation
    result = graph.invoke(
        {
            "alert": "Sentinel ingestion stopped"
        },
        config=config
    )

    print("\nFirst execution result:")
    print(result)
