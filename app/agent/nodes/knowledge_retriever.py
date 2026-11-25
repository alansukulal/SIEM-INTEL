
from app.agent.state import InvestigationState
from app.tools.vector_store import search_knowledge


MAX_RESULTS_PER_SOURCE = 3
MAX_DOCUMENT_CHARS = 1500
MIN_RELEVANCE_SCORE = 0.0
MAX_HISTORY_MESSAGES = 6


def knowledge_retriever_node(state: InvestigationState) -> dict:
    alert = state.get("alert", "")
    next_reason = state.get("next_investigation_reason", "")
    raw_plan = state.get("plan", "")
    conversation_history = state.get("conversation_history", [])

    # Start with the latest user request.
    search_parts = [alert]

    # Include recent user messages to preserve follow-up context.
    
    # Include recent user messages to preserve follow-up context.
    previous_user_messages = [
        message.get("content", "").strip()
        for message in conversation_history[:-1]
        if message.get("role") == "user"
        and message.get("content", "").strip()
    ]

    # Remove duplicates while preserving message order.
    previous_user_messages = list(
        dict.fromkeys(previous_user_messages)
    )

    if previous_user_messages:
        search_parts.extend(
            previous_user_messages[-MAX_HISTORY_MESSAGES:]
        )

    # Include the investigation objective when available.
    if raw_plan.strip():
        search_parts.append(raw_plan)

    if next_reason.strip():
        search_parts.append(next_reason)

    # Bound the retrieval query to avoid excessive context.
    search_query = "\n".join(search_parts)[:4000]


    # Retrieve runbooks and schemas separately.
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

            retrieved.append(
                {
                    "document": document[:MAX_DOCUMENT_CHARS],
                    "metadata": metadata,
                    "distance": distance,
                }
            )

    return {"knowledge": retrieved}
