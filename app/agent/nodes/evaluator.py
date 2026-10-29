
import json

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.evaluation import EvaluationResult


def evaluator_node(state: InvestigationState) -> dict:
    # A failed query must not be treated as evidence of an outage.
    if state.get("investigation_status") == "failed":
        return {
            "finding": (
                "Sentinel query execution failed. "
                "The alert could not be evaluated from this query."
            ),
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        }

    evidence = state.get("evidence", [])
    history = state.get("investigation_history", [])
    attempts = state.get("investigation_attempts", 0)
    max_steps = state.get("max_investigation_steps", 10)

    # The plan is JSON text produced by the planner.
    raw_plan = state.get("plan", "")
    try:
        plan = json.loads(raw_plan) if raw_plan else {}
    except (json.JSONDecodeError, TypeError):
        plan = {"objective": raw_plan}

    plan_context = json.dumps(plan, default=str)[:2500]

    # Bound evidence and history to control prompt size.
    if isinstance(evidence, list):
        evidence_context = json.dumps(
            evidence[-5:], default=str
        )[:3000]
    else:
        evidence_context = str(evidence)[:3000]

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
        history_items, default=str
    )[:2500]

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

Evidence collected:
{evidence_context}

Investigation history:
{history_context}

Investigation steps completed: {attempts}
Maximum investigation steps: {max_steps}

Your task is to determine whether the investigation objective has
been answered by the available evidence.

Rules:
1. Evaluate the original objective and its success criteria, not
   unrelated questions.
2. Distinguish between logs being present, logs being absent in the
   searched time range, and evidence being insufficient.
3. Do not claim that an entire table is empty merely because a query
   returned no rows for a limited time range or filter.
4. Do not claim an outage or healthy ingestion without supporting evidence.
5. Consider all available evidence and previous query history.
6. If the objective is answered, set needs_more_investigation=False.
7. If an important question remains unanswered, request another query
   only when a useful, non-duplicative query could resolve that gap.
8. If the evidence is inconclusive and no useful query is apparent,
   explain the limitation and stop.
9. If the step budget is exhausted and the objective remains
   unanswered, set needs_more_investigation=True and explain what
   remains unresolved. The graph will mark the investigation incomplete.
10. Keep findings concise, factual, and evidence-based.
11. Do not confuse reaching the step limit with answering the objective.

Return:
- finding: What the evidence establishes and any limitations.
- needs_more_investigation: Whether important questions remain.
- next_investigation_reason: The specific unresolved question, or
  an empty string if no further investigation is needed.
"""

    result: EvaluationResult = LLMClient().invoke_structured(
        prompt,
        EvaluationResult,
    )

    # Preserve the model's decision. Graph routing determines whether
    # an unresolved investigation can continue within its step budget.
    return {
        "finding": result.finding,
        "needs_more_investigation": result.needs_more_investigation,
        "next_investigation_reason": (
            result.next_investigation_reason
            if result.needs_more_investigation
            else ""
        ),
    }
