
from app.agent.state import InvestigationState
from app.tools.vector_store import search_knowledge


def knowledge_retriever_node(state: InvestigationState) -> dict:
    alert = state.get("alert", "")
    next_reason = state.get("next_investigation_reason", "")

    search_query = "\n".join(
        part for part in [alert, next_reason] if part.strip()
    )

    # Retrieve runbook instructions.
    runbook_results = search_knowledge(
        query=search_query,
        n_results=3,
        source_type="runbook",
    )

    # Retrieve table schemas separately.
    schema_results = search_knowledge(
        query=search_query,
        n_results=3,
        source_type="table_schema",
    )

    # Keep both kinds of knowledge available to the generator.
    results = runbook_results + schema_results

    knowledge = [
        {
            "document": result["document"],
            "metadata": result["metadata"],
            "distance": result["distance"],
        }
        for result in results
    ]

    return {"knowledge": knowledge}
