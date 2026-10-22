from app.agent.state import InvestigationState
from app.llm.client import LLMClient


def evaluator_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    query = state["query"]
    evidence = state["evidence"]

    prompt = f"""
You are a SOC investigation evaluator.

Analyze the investigation evidence below and provide a concise finding.

Alert:
{alert}

Executed KQL:
{query}

Evidence:
{evidence}

Explain:
1. What the evidence shows.
2. Whether the evidence supports or contradicts the alert.
3. Whether more investigation is required.

Do not invent facts that are not present in the evidence.
"""

    llm = LLMClient()

    response = llm.invoke(prompt)
    if evidence:
        needs_more_investigation=False

    else:
        needs_more_investigation=True

    return {
        "finding": response.content,
        "needs_more_investigation":needs_more_investigation,
    }