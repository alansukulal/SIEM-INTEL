
from app.agent.state import InvestigationState
from app.tools.vector_store import search_knowledge


MAX_RESULTS_PER_SOURCE = 3
MAX_DOCUMENT_CHARS = 1500
MIN_RELEVANCE_SCORE = 0.0


def knowledge_retriever_node(state: InvestigationState) -> dict:
    alert = state.get("alert", "")
    next_reason = state.get("next_investigation_reason", "")
    raw_plan = state.get("plan", "")

    # Include the objective when a plan already exists.
    search_parts = [alert]

    if raw_plan.strip():
        search_parts.append(raw_plan)

    if next_reason.strip():
        search_parts.append(next_reason)

    search_query = "\n".join(search_parts)

    # Retrieve runbooks and schemas separately so their source types
    # remain explicit.
    retrieved = []

    for source_type in ("runbook", "table_schema"):
        results = search_knowledge(
            query=search_query,
            n_results=MAX_RESULTS_PER_SOURCE,
            source_type=source_type,
        )

        for result in results:
            document = str(result.get("document", "")).strip()
            metadata = result.get("metadata", {})
            distance = result.get("distance")

            if not document:
                continue

            # Vector-store distance is not universally normalized.
            # Do not apply a numeric cutoff until its metric is verified.
            retrieved.append(
                {
                    "document": document[:MAX_DOCUMENT_CHARS],
                    "metadata": metadata,
                    "distance": distance,
                }
            )

    return {"knowledge": retrieved}
