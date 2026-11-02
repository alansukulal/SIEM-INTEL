
import json

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.evaluation import EvaluationResult


def _format_context(value, limit=4000):
    """Safely format tool context while controlling prompt size."""
    try:
        return json.dumps(value, default=str)[:limit]
    except (TypeError, ValueError):
        return str(value)[:limit]


def evaluator_node(state: InvestigationState) -> dict:
    evidence = state.get("evidence", [])
    history = state.get("investigation_history", [])

    tool_results = state.get("tool_results", [])
    tool_errors = state.get("tool_errors", [])
    tool_calls = state.get("tool_calls", [])

    attempts = state.get("investigation_attempts", 0)
    max_steps = state.get("max_investigation_steps", 10)

    # Parse the structured investigation plan.
    raw_plan = state.get("plan", "")

    try:
        plan = json.loads(raw_plan) if raw_plan else {}
    except (json.JSONDecodeError, TypeError):
        plan = {"objective": raw_plan}

    plan_context = _format_context(plan, 2500)

    # Bound existing Sentinel evidence.
    evidence_context = _format_context(
        evidence[-5:] if isinstance(evidence, list) else evidence,
        3000,
    )

    # Include results returned by dynamically selected tools.
    tool_results_context = _format_context(
        tool_results[-10:],
        5000,
    )

    # Include failures for transparency.
    tool_errors_context = _format_context(
        tool_errors[-5:],
        2000,
    )

    tool_calls_context = _format_context(
        tool_calls[-10:],
        2000,
    )

    history_items = []

    for item in history[-4:]:
        previous_evidence = item.get("evidence", [])

        history_items.append({
            "query": item.get("query", ""),
            "status": item.get("status", "unknown"),
            "evidence_row_count": (
                len(previous_evidence)
                if isinstance(previous_evidence, list)
                else None
            ),
        })

    history_context = _format_context(history_items, 2500)

    prompt = f"""
You are a SOC investigation evaluator for {state.get("siem", "")}.

Original alert or question:
{state.get("alert", "")}

Investigation plan:
{plan_context}

Latest executed KQL:
{state.get("query", "")}

Latest query execution status:
{state.get("investigation_status", "unknown")}

Latest investigation error:
{state.get("investigation_error", "")}

Sentinel evidence:
{evidence_context}

Results from dynamically selected tools:
{tool_results_context}

Tool calls:
{tool_calls_context}

Tool execution errors:
{tool_errors_context}

Investigation history:
{history_context}

Investigation steps completed: {attempts}
Maximum investigation steps: {max_steps}

Your task is to determine whether the investigation objective
has been answered by the available evidence.

Rules:
1. Evaluate the original objective and investigation plan.
2. Consider Sentinel evidence and results from all other tools.
3. Distinguish verified facts from assumptions and missing evidence.
4. A failed Sentinel query does not prove the alert is true or false.
5. A failed tool does not invalidate successful evidence.
6. If Sentinel fails, consider whether another available capability
   could help answer the unresolved question.
7. Do not claim an outage or healthy ingestion without supporting evidence.
8. Consider previous actions and avoid duplicate investigation.
9. Request another investigation action only if it can resolve an
   important unanswered question.
10. If the objective is answered, set needs_more_investigation=False.
11. If the evidence is inconclusive and no useful action remains,
    explain the limitation and stop.
12. If the investigation step budget is exhausted, stop requesting
    further actions and explain what remains unresolved.
13. Avoid repeating a previous investigation action unless new
    evidence provides a valid reason.
14. Keep findings concise, factual, and evidence-based.

Return:
- finding: What the available evidence establishes and its limitations.
- needs_more_investigation: Whether important questions remain.
- next_investigation_reason: The specific unresolved question,
  or an empty string if no further investigation is needed.
"""

    result: EvaluationResult = LLMClient().invoke_structured(
        prompt,
        EvaluationResult,
    )

    # Enforce the investigation budget in application code.
    needs_more_investigation = (
        result.needs_more_investigation
        and attempts < max_steps
    )

    return {
        "finding": result.finding,
        "needs_more_investigation": needs_more_investigation,
        "next_investigation_reason": (
            result.next_investigation_reason
            if needs_more_investigation
            else ""
        ),
    }
