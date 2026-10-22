
import re

from app.agent.state import InvestigationState


BLOCKED_OPERATORS = (
    ".drop",
    ".delete",
    ".set",
    ".append",
    ".ingest",
    ".alter",
    ".create",
    ".rename",
    ".move",
    ".clear",
    ".purge",
    ".replace",
)

BLOCKED_KEYWORDS = (
    "externaldata",
    "external_table",
    "evaluate",
    "invoke",
    "union",
    "join",
)


def kql_validator_node(state: InvestigationState) -> dict:
    kql = state["query"].strip()
    errors: list[str] = []

    if not kql:
        errors.append("KQL query is empty.")
    else:
        if "```" in kql:
            errors.append("Remove Markdown code fences from KQL.")

        # This initial policy permits one query statement only.
        if ";" in kql:
            errors.append("Multiple statements are not allowed.")

        # Require a table from the retrieved knowledge.
        allowed_tables = {
            item.get("metadata", {}).get("table")
            for item in state.get("knowledge", [])
            if item.get("metadata", {}).get("table")
        }

        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\b", kql)

        if not match:
            errors.append(
                "Query must start with a documented table name."
            )
        else:
            first_table = match.group(1)

            if first_table not in allowed_tables:
                errors.append(
                    f"Table '{first_table}' is not in the retrieved "
                    "knowledge allow-list."
                )

        lowered_kql = kql.lower()

        for operator in BLOCKED_OPERATORS:
            if re.search(
                rf"(?<![A-Za-z0-9_])"
                rf"{re.escape(operator)}"
                rf"(?![A-Za-z0-9_])",
                lowered_kql,
            ):
                errors.append(
                    f"Potentially unsafe operation detected: {operator}"
                )

        for keyword in BLOCKED_KEYWORDS:
            if re.search(
                rf"\b{re.escape(keyword)}\b",
                lowered_kql,
            ):
                errors.append(
                    f"Disallowed KQL keyword detected: {keyword}"
                )

    return {
        "kql_valid": not errors,
        "kql_validation_errors": errors,
    }
