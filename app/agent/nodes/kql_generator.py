
from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.kql import KQLGenerationResult


def kql_generator_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]
    errors = state.get("kql_validation_errors", [])
    knowledge = state.get("knowledge", [])
    history = state.get("investigation_history", [])

    knowledge_context = "\n\n".join(
        (
            f"Type: {item.get('metadata', {}).get('type', 'unknown')}\n"
            f"Title: {item.get('metadata', {}).get('title', 'Untitled')}\n"
            f"Content:\n{item.get('document', '')}"
        )
        for item in knowledge
    )

    previous_query = state.get("query", "")
    next_reason = state.get("next_investigation_reason", "")
    evidence = state.get("evidence", [])
    investigation_attempts = state.get("investigation_attempts", 0)


    history_context = "\n\n".join(
        (
            f"Previous query: {item.get('query', '')}\n"
            f"Execution status: {item.get('status', 'unknown')}\n"
            f"Evidence row count: {len(item.get('evidence', []))}"
        )
        for item in history[-4:]
    ) or "No previous investigation queries."

    # Keep the latest evidence small instead of resending every record.
    latest_evidence = evidence[:5] if isinstance(evidence, list) else evidence
    evidence_context = str(latest_evidence)[:3000]

    # Keep retrieved knowledge bounded while preserving schema context.
    knowledge_context = "\n\n".join(
        (
            f"Type: {item.get('metadata', {}).get('type', 'unknown')}\n"
            f"Title: {item.get('metadata', {}).get('title', 'Untitled')}\n"
            f"Content:\n{item.get('document', '')[:2000]}"
        )
        for item in knowledge[:4]
    )


    prompt = f"""
You are an expert Microsoft Sentinel KQL query generator.

Generate exactly one read-only KQL query to investigate the alert.

SIEM:
{siem}

Alert:
{alert}

Retrieved knowledge:
{knowledge_context}

Previous query:
{previous_query}

Evidence from the latest query:
{evidence}

Complete investigation history:
{history_context}

Reason for further investigation:
{next_reason}

Previous validation errors:
{errors}

Investigation attempts completed:
{investigation_attempts}

Requirements:
1. Use a table explicitly present in the retrieved knowledge.
2. Use only columns documented for that table.
3. Do not invent tables, columns, or evidence.
4. Generate one query statement, not multiple statements.
5. Do not use write, schema-changing, or data-management commands.
6. Do not use union, join, evaluate, invoke, or externaldata.
7. Correct previous validation errors when provided.
8. Address the specific unanswered question in the investigation reason.
9. Consider all previous queries and their evidence.
10. Do not repeat any previously executed query.
11. Prefer a meaningfully different investigation that adds useful evidence.
12. If the knowledge is insufficient, return an empty KQL query and
    explain the limitation in the reason field.
13. Do not include Markdown code fences.

Return:
- kql: the KQL query
- reason: a concise explanation of the query or why it cannot be
  generated safely.
"""

    llm = LLMClient()
    result = llm.invoke_structured(prompt, KQLGenerationResult)

    new_query = result.kql.strip()
    normalized_new_query = " ".join(new_query.lower().split())

    # Do not repeat any successfully or unsuccessfully executed query.
    executed_queries = {
        " ".join(item.get("query", "").lower().split())
        for item in history
        if item.get("query")
    }

    if new_query and normalized_new_query in executed_queries:
        return {
            "query": "",
            "kql_reason": (
                "The generated query matches a previously executed query. "
                "A different query is required to add new evidence."
            ),
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    # Preserve the existing immediate-repeat safeguard.
    if (
        investigation_attempts > 0
        and next_reason
        and new_query
        and normalized_new_query
        == " ".join(previous_query.lower().split())
        and not errors
    ):
        return {
            "query": "",
            "kql_reason": (
                "The generated query repeated the previous query. "
                "A meaningfully different query is required."
            ),
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    return {
        "query": new_query,
        "kql_reason": result.reason,
        "kql_attempts": state.get("kql_attempts", 0) + 1,
    }
