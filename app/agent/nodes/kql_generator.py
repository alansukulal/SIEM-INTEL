
from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.kql import KQLGenerationResult


def kql_generator_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]
    errors = state.get("kql_validation_errors", [])
    knowledge = state.get("knowledge", [])
    previous_query = state.get("query", "")
    next_reason = state.get("next_investigation_reason", "")
    evidence = state.get("evidence", [])
    investigation_attempts = state.get("investigation_attempts", 0)

    prompt = f"""
You are an expert Microsoft Sentinel KQL query generator.

Generate exactly one read-only KQL query to investigate the alert.

SIEM:
{siem}

Alert:
{alert}

Retrieved knowledge:
{knowledge}

Previous query:
{previous_query}

Previous evidence:
{evidence}

Reason for further investigation:
{next_reason}

Previous validation errors:
{errors}

Requirements:
1. Use a table explicitly present in the retrieved knowledge.
2. Use only columns documented for that table.
3. Do not invent tables, columns, or evidence.
4. Generate one query statement, not multiple statements.
5. Do not use write, schema-changing, or data-management commands.
6. Do not use union, join, evaluate, invoke, or externaldata.
7. Correct previous validation errors when provided.
8. If more investigation was requested, address the specific unanswered
   question in the reason above.
9. When previous evidence exists, use it to guide the next query.
10. Do not blindly repeat the previous query.
11. If the retrieved knowledge is insufficient, return an empty KQL
    query and explain the limitation in the reason field.
12. Do not include Markdown code fences.

Return:
- kql: the KQL query
- reason: a concise explanation of the query or why it cannot be
  generated safely.
"""

    llm = LLMClient()
    result = llm.invoke_structured(prompt, KQLGenerationResult)

    new_query = result.kql.strip()

    # Avoid blindly executing the same query during a follow-up
    # investigation. Do not block validation-error correction retries.
    if (
        investigation_attempts > 0
        and next_reason
        and new_query
        and new_query == previous_query.strip()
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
