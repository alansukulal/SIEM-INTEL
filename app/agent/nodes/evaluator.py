
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

    evidence = state.get("evidence", [])
    history = state.get("investigation_history", [])
    attempts = state.get("investigation_attempts", 0)
    max_steps = state.get("max_investigation_steps", 10)

    # Do not request more work when the investigation budget is exhausted.
    if attempts >= max_steps:
        return {
            "finding": (
                "The investigation reached its maximum step limit. "
                "Findings are based on the evidence collected so far."
            ),
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        }
    
    latest_evidence = evidence[:5] if isinstance(evidence, list) else evidence
    evidence_context = str(latest_evidence)[:3000]

    history_context = "\n\n".join(
        (
            f"Query: {item.get('query', '')}\n"
            f"Status: {item.get('status', 'unknown')}\n"
            f"Evidence row count: {len(item.get('evidence', []))}"
        )
        for item in history[-4:]
    ) or "No previous investigation queries."


    prompt = f"""
You are a SOC investigation evaluator for Microsoft Sentinel.

Alert:
{state.get("alert", "")}

Latest executed KQL:
{state.get("query", "")}

Evidence from the latest query:
{evidence_context}

Complete investigation history, including previous queries and results:
{history_context}

Current investigation step: {attempts}
Maximum investigation steps: {max_steps}

Evaluate the evidence and decide whether more investigation is needed.

Explain:
1. What the collected evidence actually shows.
2. Whether it supports, contradicts, or is insufficient to assess the alert.
3. What important question remains unanswered, if any.
4. If another query is necessary, describe a specific next investigation.

Rules:
- Do not invent facts or claim that missing evidence proves an alert is false.
- Consider the latest evidence together with all previous investigation results.
- Check the history before requesting further investigation.
- Do not request a query that merely repeats a previous query or investigation.
- Request further investigation only if it could answer an important,
  unanswered question.
- If the evidence is sufficient, return needs_more_investigation=False.
- If further investigation is needed, make next_investigation_reason
  specific enough to guide a meaningfully different KQL query.
- If the evidence is inconclusive and no useful next query is apparent,
  explain the limitation and stop.
"""

    llm = LLMClient()
    result: EvaluationResult = llm.invoke_structured(
        prompt,
        EvaluationResult,
    )

    return {
        "finding": result.finding,
        "needs_more_investigation": result.needs_more_investigation,
        "next_investigation_reason": (
            result.next_investigation_reason
            if result.needs_more_investigation
            else ""
        ),
    }
