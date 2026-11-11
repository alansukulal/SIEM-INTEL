
import logging

from app.agent.state import InvestigationState
from app.tools.kql_safety import validate_kql

logger = logging.getLogger(__name__)


def kql_validator_node(state: InvestigationState) -> dict:
    query = state.get("query") or ""

    errors = validate_kql(
        query=query,
        knowledge=state.get("knowledge", []),
        investigation_history=state.get("investigation_history", []),
    )

    correction_attempts = state.get(
        "kql_correction_attempts",
        0,
    )

    if errors:
        correction_attempts += 1
        logger.warning(
            "KQL validation failed. Correction attempt: %s. Errors: %s",
            correction_attempts,
            errors,
        )
    else:
        correction_attempts = 0
        logger.info("KQL validation passed.")

    return {
        "kql_valid": not errors,
        "kql_validation_errors": errors,
        "kql_correction_attempts": correction_attempts,
    }
