from typing import Any

from app.tools.vector_store import search_knowledge


def knowledge_search(
    query: str,
    source_type: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Search the SIEM knowledge base for relevant runbooks and schemas.
    """

    if not query or not query.strip():
        raise ValueError("Knowledge search query cannot be empty.")

    if limit < 1 or limit > 10:
        raise ValueError("Limit must be between 1 and 10.")

    allowed_sources = {"runbook", "table_schema"}

    if source_type and source_type not in allowed_sources:
        raise ValueError(
            f"Unsupported source type: {source_type}"
        )

    results = search_knowledge(
        query=query.strip(),
        n_results=limit,
        source_type=source_type,
    )

    return [
        {
            "document": item.get("document", ""),
            "metadata": item.get("metadata", {}),
            "distance": item.get("distance"),
        }
        for item in results
    ]