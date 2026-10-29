
import json

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.investigation_plan import InvestigationPlan


def planner_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]
    knowledge = state.get("knowledge", [])

    prompt = f"""
You are planning a SIEM investigation.

Original alert or question:
{alert}

SIEM platform:
{siem}

Retrieved runbooks, documentation, and relevant knowledge:
{json.dumps(knowledge, default=str)}

Create a concise investigation plan.

Requirements:
- Identify the exact question that must be answered.
- Specify the minimum evidence required.
- Define when the question is sufficiently answered.
- Prefer the simplest safe investigation that can establish the facts.
- Do not assume an outage merely because an alert reports one.
- Do not assume logs are healthy merely because some recent events exist.
- Do not invent table names, fields, or facts.
- Use retrieved knowledge where relevant.
- Avoid unrelated checks and unnecessary query iterations.
- If the evidence cannot establish the answer, describe the limitation.
- Do not generate KQL; the query generator handles that separately.
"""

    client = LLMClient()
    plan = client.invoke_structured(prompt, InvestigationPlan)

    return {"plan": plan.model_dump_json(indent=2)}
