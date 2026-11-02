
from app.agent.state import InvestigationState
from app.tools.kql_safety import validate_kql


def kql_validator_node(state: InvestigationState) -> dict:
    errors = validate_kql(
        query=state.get("query", ""),
        knowledge=state.get("knowledge", []),
        investigation_history=state.get(
            "investigation_history", []
        ),
    )

    correction_attempts = state.get(
        "kql_correction_attempts", 0
    )

    if errors:
        correction_attempts += 1
    else:
        correction_attempts = 0

    return {
        "kql_valid": not errors,
        "kql_validation_errors": errors,
        "kql_correction_attempts": correction_attempts,
    }
