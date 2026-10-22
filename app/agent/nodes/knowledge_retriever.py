
from app.agent.state import InvestigationState
from app.tools.vector_store import search_knowledge


def knowledge_retriever_node(state: InvestigationState) -> dict:
    alert = state["alert"]

    results = search_knowledge(
        query=alert,
        n_results=3,
    )

    knowledge = [
        {
            "document": result["document"],
            "metadata": result["metadata"],
            "distance": result["distance"],
        }
        for result in results
    ]

    return {"knowledge": knowledge}
