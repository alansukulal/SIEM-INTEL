
from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.kql import KQLGenerationResult


def kql_generator_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]
    errors = state.get("kql_validation_errors", [])
    knowledge = state.get("knowledge", [])

    prompt = f"""
You are an expert Microsoft Sentinel KQL query generator.

Generate exactly one read-only KQL query to investigate the alert.

SIEM:
{siem}

Alert:
{alert}

Retrieved knowledge:
{knowledge}

Previous validation errors:
{errors}

Requirements:
1. Use a table explicitly present in the retrieved knowledge.
2. Use only columns documented for that table.
3. Do not invent tables, columns, or evidence.
4. Generate one query statement, not multiple statements.
5. Do not use write, schema-changing, or data-management commands.
6. Do not use union, join, evaluate, invoke, or externaldata.
7. If validation errors are provided, correct the query to address them.
8. If the retrieved knowledge is insufficient, do not invent a schema.
   Explain the limitation in the reason field and return an empty KQL
   query rather than guessing.
9. Do not include Markdown code fences.

Return:
- kql: the KQL query
- reason: a concise explanation of the query or why it cannot be
  generated safely.
"""

    llm = LLMClient()

    result = llm.invoke_structured(
        prompt,
        KQLGenerationResult,
    )

    return {
        "query": result.kql.strip(),
        "kql_reason": result.reason,
        "kql_attempts": state.get("kql_attempts", 0) + 1,
    }
