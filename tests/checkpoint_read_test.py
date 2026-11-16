
import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
    1
)


class InvestigationState(TypedDict):
    alert: str
    plan: str
    finding: str


# Rebuild the same graph structure
def planner(state):
    return {"plan": f"Investigate alert: {state['alert']}"}


def investigator(state):
    return {"finding": f"Investigation completed for: {state['alert']}"}


builder = StateGraph(InvestigationState)

builder.add_node("planner", planner)
builder.add_node("investigator", investigator)

builder.add_edge(START, "planner")
builder.add_edge("planner", "investigator")
builder.add_edge("investigator", END)


with PostgresSaver.from_conn_string(
    CHECKPOINT_DATABASE_URL
) as checkpointer:

    checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "thread-demo-001"
        }
    }

    # Read the previously saved state
    snapshot = graph.get_state(config)

    print("Persisted state:")
    print(snapshot.values)

    print("\nPersisted thread:")
    print(snapshot.config["configurable"]["thread_id"])

    print("\nCheckpoint history:")

    for checkpoint in graph.get_state_history(config):
        print(checkpoint.config["configurable"]["checkpoint_id"])
        print(checkpoint.values)
        print("---")
