
from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.evaluation import EvaluationResult


def evaluator_node(state: InvestigationState) -> dict:
    # A failed query is not the same as an empty result.
    if state.get("investigation_status") == "failed":
        return {
            "finding": (
                "Sentinel query execution failed. "
                "The alert cannot be evaluated from this investigation."
            ),
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        }

    evidence = state["evidence"]

    # A successful query returning no rows is a valid outcome.
    if not evidence:
        return {
            "finding": (
                "The query completed but returned no matching events. "
                "This alone does not prove the alert is false."
            ),
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        }

    prompt = f"""
You are a SOC investigation evaluator.

Alert:
{state["alert"]}

Executed KQL:
{state["query"]}

Evidence:
{evidence}

Evaluate the evidence and decide whether more investigation is needed.

Explain:
1. What the evidence shows.
2. Whether it supports or contradicts the alert.
3. What important question remains unanswered, if any.

Rules:
- Do not invent facts.
- Request further investigation only when additional evidence could
  help answer an important unanswered question.
- If more investigation is needed, specify what to investigate next.
"""

    llm = LLMClient()
    result: EvaluationResult = llm.invoke_structured(
        prompt,
        EvaluationResult,
    )

    return {
        "finding": result.finding,
        "needs_more_investigation": result.needs_more_investigation,
        "next_investigation_reason": result.next_investigation_reason,
    }
