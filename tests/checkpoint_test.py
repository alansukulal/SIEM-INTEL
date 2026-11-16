
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from dotenv import load_dotenv
import os


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CHECKPOINT_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://",
    "postgresql://",
    1
)

# 1. Define graph state
class InvestigationState(TypedDict):
    alert: str
    plan: str
    finding: str


# 2. Define nodes
def planner(state: InvestigationState):
    print("Planner executing...")

    return {
        "plan": f"Investigate alert: {state['alert']}"
    }


def investigator(state: InvestigationState):
    print("Investigator executing...")

    return {
        "finding": f"Investigation completed for: {state['alert']}"
    }


# 3. Build graph
builder = StateGraph(InvestigationState)

builder.add_node("planner", planner)
builder.add_node("investigator", investigator)

builder.add_edge(START, "planner")
builder.add_edge("planner", "investigator")
builder.add_edge("investigator", END)


# 4. Configure PostgreSQL checkpointer
with PostgresSaver.from_conn_string(CHECKPOINT_DATABASE_URL) as checkpointer:

    checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "thread-demo-001"
        }
    }

    # 5. Execute graph
    result = graph.invoke(
        {
            "alert": "Sentinel ingestion stopped",
            "plan": "",
            "finding": ""
        },
        config=config
    )

    print("\nFinal investigation state:")
    print(result)

    # 6. Inspect saved checkpoint
    print("\nSaved checkpoints:")

    for checkpoint in graph.get_state_history(config):
        print("Checkpoint ID:", checkpoint.config["configurable"]["checkpoint_id"])
        print("State:", checkpoint.values)
        print("---")
