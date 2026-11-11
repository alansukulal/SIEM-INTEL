
import json
import logging
import re
from typing import Any

from azure.core.exceptions import AzureError

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.kql import KQLGenerationResult
from app.tools.sentinel import SentinelClient, SentinelQueryError


logger = logging.getLogger(__name__)


def _format_evidence(
    evidence: Any,
    limit: int = 5,
) -> str:
    """Keep evidence context small enough to control token usage."""
    if not isinstance(evidence, list):
        return str(evidence)[:2500]

    return json.dumps(evidence[:limit], default=str)[:2500]


def _extract_requested_table(alert: str) -> str | None:
    """Extract a simple table identifier explicitly mentioned in the alert."""
    patterns = [
        r"\btable\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        r"\bon\s+([A-Za-z_][A-Za-z0-9_]*)\s+table\b",
        r"\b([A-Za-z_][A-Za-z0-9_]*_CL)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, alert, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def _get_known_schema_tables(knowledge: list[dict]) -> set[str]:
    """Return tables with actual documented column definitions."""
    known_tables = set()

    for item in knowledge:
        metadata = item.get("metadata", {})

        if metadata.get("type") != "table_schema":
            continue

        document = str(item.get("document", ""))

        has_columns = bool(
            re.search(
                r"(?im)^\s*[-*]\s*[\w.-]+\s*:\s*[\w<>(), ]+\s*$",
                document,
            )
        )

        table_name = metadata.get("table") or metadata.get("title")

        if table_name and has_columns:
            known_tables.add(str(table_name).lower())

    return known_tables


def _discover_schema_knowledge(
    alert: str,
    knowledge: list[dict],
) -> tuple[list[dict], str | None]:
    """
    Discover live Sentinel schema when the requested table is not
    documented in the retrieved table-schema knowledge.
    """
    requested_table = _extract_requested_table(alert)

    if not requested_table:
        return knowledge, None

    known_tables = _get_known_schema_tables(knowledge)

    if requested_table.lower() in known_tables:
        return knowledge, None

    logger.info(
        "Table %s is not present in retrieved schema knowledge. "
        "Attempting live schema discovery.",
        requested_table,
    )

    logger.info(
        "SCHEMA DEBUG: requested_table=%r, known_tables=%r",
        requested_table,
        sorted(known_tables),
    )

    try:
        schema = SentinelClient().get_table_schema(requested_table)

    except (SentinelQueryError, ValueError, AzureError) as exc:
        logger.warning(
            "Could not verify schema for requested table %s. Error type: %s",
            requested_table,
            type(exc).__name__,
        )

        return (
            knowledge,
            f"Could not verify the schema for '{requested_table}' "
            "in the configured Sentinel workspace. The agent stopped "
            "rather than guessing table or column names. Check workspace "
            "permissions, table availability, and server diagnostics.",
        )

    if not schema:
        logger.warning(
            "Live schema discovery returned no columns for %s.",
            requested_table,
        )

        return (
            knowledge,
            f"Live schema discovery returned no columns for "
            f"'{requested_table}'. The agent cannot safely generate "
            "a query without verified column metadata.",
        )

    logger.info(
        "SCHEMA DEBUG: discovered %d columns for %s: %s",
        len(schema),
        requested_table,
        [column["name"] for column in schema],
    )

    schema_document = (
        f"## {requested_table}\n"
        "Source: live Sentinel workspace schema discovery\n"
        "Verified columns:\n"
        + "\n".join(
            f"- {column['name']}: {column['type']}"
            for column in schema
        )
    )

    updated_knowledge = list(knowledge)

    # Keep live schema at the front of knowledge for other consumers.
    updated_knowledge.insert(
        0,
        {
            "document": schema_document,
            "metadata": {
                "type": "table_schema",
                "title": requested_table,
                "table": requested_table,
                "source": "live_schema_discovery",
            },
            "distance": None,
        },
    )

    logger.info(
        "Added verified live schema for table %s to investigation context.",
        requested_table,
    )

    return updated_knowledge, None


def _build_prompt_knowledge(
    knowledge: list[dict],
    requested_table: str | None,
) -> tuple[str, str]:
    """
    Build separate RAG and live-schema contexts.

    The live schema is kept outside the RAG size limit so retrieved
    documents cannot push verified column metadata out of the prompt.
    """
    live_schema_context = ""
    regular_items = []

    # Find the live schema independently of its position in the list.
    for item in knowledge:
        metadata = item.get("metadata", {})

        if metadata.get("source") == "live_schema_discovery":
            live_schema_context = str(item.get("document", ""))
        else:
            regular_items.append(item)

    # Prefer schema documentation for the requested table, then runbooks.
    if requested_table:
        matching_schema = []
        other_items = []

        for item in regular_items:
            metadata = item.get("metadata", {})
            table_name = metadata.get("table") or metadata.get("title", "")

            if (
                metadata.get("type") == "table_schema"
                and str(table_name).lower() == requested_table.lower()
            ):
                matching_schema.append(item)
            else:
                other_items.append(item)

        regular_items = matching_schema + other_items

    knowledge_items = []

    for item in regular_items:
        if len(knowledge_items) >= 4:
            break

        metadata = item.get("metadata", {})

        knowledge_items.append(
            {
                "type": metadata.get("type", "unknown"),
                "title": metadata.get("title", "Untitled"),
                "table": metadata.get("table", ""),
                "source": metadata.get("source", ""),
                "content": str(item.get("document", ""))[:1200],
            }
        )

    knowledge_context = json.dumps(
        knowledge_items,
        default=str,
    )[:3500]

    # 372 columns may be a large document. Keep it separate from RAG.
    live_schema_context = live_schema_context[:16000]

    return knowledge_context, live_schema_context


def kql_generator_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]

    errors = state.get("kql_validation_errors", [])
    knowledge = list(state.get("knowledge", []))
    history = state.get("investigation_history", [])
    evidence = state.get("evidence", [])

    previous_query = state.get("query", "")
    next_reason = state.get("next_investigation_reason", "")
    investigation_attempts = state.get("investigation_attempts", 0)
    correction_attempts = state.get("kql_correction_attempts", 0)

    # First, use retrieved knowledge. Discover the live schema if necessary.
    knowledge, discovery_error = _discover_schema_knowledge(
        alert,
        knowledge,
    )

    if discovery_error:
        return {
            "query": "",
            "kql_reason": discovery_error,
            "knowledge": knowledge,
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    requested_table = _extract_requested_table(alert)

    # The planner stores its structured plan as JSON text.
    raw_plan = state.get("plan", "")

    try:
        plan = json.loads(raw_plan) if raw_plan else {}
    except (json.JSONDecodeError, TypeError):
        plan = {"objective": raw_plan}

    plan_context = json.dumps(plan, default=str)[:2500]

    # Keep RAG and verified live schema separate in the prompt.
    knowledge_context, live_schema_context = _build_prompt_knowledge(
        knowledge,
        requested_table,
    )

    logger.info(
        "KQL prompt context: requested_table=%r, live_schema_chars=%d",
        requested_table,
        len(live_schema_context),
    )

    if live_schema_context:
        logger.info(
            "Verified live schema is included in the KQL generation prompt."
        )

    # Keep a concise record of previous queries and their results.
    history_items = []

    for item in history[-4:]:
        previous_evidence = item.get("evidence", [])

        history_items.append(
            {
                "query": item.get("query", ""),
                "status": item.get("status", "unknown"),
                "evidence_row_count": (
                    len(previous_evidence)
                    if isinstance(previous_evidence, list)
                    else None
                ),
            }
        )

    history_context = json.dumps(
        history_items,
        default=str,
    )[:2500]

    evidence_context = _format_evidence(evidence)

    prompt = f"""
You are a Microsoft Sentinel KQL query generator.

Generate one safe, read-only KQL query that advances the investigation.

SIEM:
{siem}

Original alert or question:
{alert}

Investigation plan:
{plan_context}

Retrieved RAG knowledge:
{knowledge_context}

Verified live Sentinel schema:
{live_schema_context or "No live schema was discovered for this investigation."}

Evidence collected so far:
{evidence_context}

Previous investigation history:
{history_context}

Previous query:
{previous_query}

Specific unanswered question, if any:
{next_reason or "Use the investigation plan to determine the next necessary evidence."}

Previous validation errors:
{json.dumps(errors, default=str)[:1500]}
KQL CORRECTION ATTEMPTS:
{correction_attempts}

Investigation attempts completed:
{investigation_attempts}


Previous validation errors must be corrected.
If the same query cannot be made safe, return an empty query
and explain why in the reason field.

Rules:
1. Address the investigation objective, not unrelated questions.
2. On the first attempt, gather the minimum evidence needed to answer
   the objective. On follow-up attempts, address the specific unanswered
   question.
3. Consider existing evidence before requesting more data.
4. Do not generate another query merely because more investigation is possible.
5. Never repeat a previously executed query.
6. Use only tables and columns supported by retrieved runbooks,
   documented schemas, or verified live Sentinel schema metadata.
7. Prefer a relevant runbook query when one applies. Adapt it only when
   necessary to answer the current investigation.
8. Live schema metadata is authoritative for the discovered table's columns.
9. When live schema is provided, use its verified column names and types.
10. Do not reject a table merely because its schema was absent from RAG.
11. For a log-outage investigation, prefer a simple recent-event timestamp
    query before attempting more complex host-level analysis.
12. For outage checks, use TimeGenerated when it is verified in the schema.
    Summarize the latest event time using appropriate verified columns.
13. If neither retrieved knowledge nor verified live schema supports
    a safe query, return an empty query and explain the limitation.
14. Generate exactly one read-only KQL statement.
15. The query must start with a documented table name.
16. Do not use let statements, semicolons, or multiple statements.
17. Do not use union, join, evaluate, invoke, or externaldata.
18. Do not use write, schema-changing, or data-management commands.
19. Correct previous validation errors when possible.
20. Do not invent data, table names, columns, or findings.
21. Do not include Markdown code fences.

Return the query in the kql field and a concise explanation in the reason field.
"""

    result = LLMClient().invoke_structured(
        prompt,
        KQLGenerationResult,
    )

    new_query = result.kql.strip()
    normalized_new_query = " ".join(new_query.lower().split())

    # Do not execute a query that has already been tried.
    executed_queries = {
        " ".join(item.get("query", "").lower().split())
        for item in history
        if item.get("query")
    }

    if new_query and normalized_new_query in executed_queries:
        return {
            "query": "",
            "kql_reason": (
                "The generated query duplicates a previous investigation "
                "query. Stopping this query attempt to avoid repeated work."
            ),
            "knowledge": knowledge,
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    # Preserve the immediate-repeat safeguard.
    if (
        investigation_attempts > 0
        and next_reason
        and new_query
        and normalized_new_query == " ".join(previous_query.lower().split())
        and not errors
    ):
        return {
            "query": "",
            "kql_reason": (
                "The generated query repeats the previous query. "
                "No duplicate execution should occur."
            ),
            "knowledge": knowledge,
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    return {
        "query": new_query,
        "kql_reason": result.reason,
        "knowledge": knowledge,
        "kql_attempts": state.get("kql_attempts", 0) + 1,
    }
