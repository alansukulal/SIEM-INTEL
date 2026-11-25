
import json

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.investigation_plan import InvestigationPlan


MAX_RECENT_MESSAGES = 8


def planner_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]
    knowledge = state.get("knowledge", [])
    conversation_history = state.get("conversation_history", [])

    # Remove the latest user message if it is already
    # represented by the current alert.
    previous_messages = conversation_history

    if (
        previous_messages
        and previous_messages[-1].get("role") == "user"
        and previous_messages[-1].get("content", "").strip()
        == alert.strip()
    ):
        previous_messages = previous_messages[:-1]

    # Preserve the original user objective and recent context.
    if len(previous_messages) > MAX_RECENT_MESSAGES:
        first_message = previous_messages[:1]
        recent_messages = previous_messages[-MAX_RECENT_MESSAGES:]

        conversation_context = first_message + [
            message
            for message in recent_messages
            if message not in first_message
        ]
    else:
        conversation_context = previous_messages

    prompt = f"""
You are planning a SIEM investigation.

Current user request:
{alert}

SIEM platform:
{siem}

Previous conversation:
{json.dumps(conversation_context, default=str)}

Retrieved runbooks, documentation, and relevant knowledge:
{json.dumps(knowledge, default=str)}

Create a concise investigation plan.

Conversation handling:
- Use previous messages to understand references and follow-up questions.
- Interpret phrases such as "that table", "those events", or "last 7 days"
  using the relevant conversation context.
- Preserve the original investigation objective unless the user explicitly
  changes it.
- Treat the current user request as the immediate task.
- Do not repeat previous investigations unnecessarily.
- Do not treat previous assistant findings as verified evidence for a new
  query; use them as context only.
- If the current request is unrelated or introduces a new objective,
  plan accordingly.

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
- Identify candidate SIEM tables needed for the investigation.
- Use table names supported by retrieved schema knowledge or conversation context.
- Do not invent table names.
- Select only the minimum necessary tables.
- Return an empty table list if no SIEM table is required.
- Candidate tables must be verified before KQL generation.
"""

    client = LLMClient()
    plan = client.invoke_structured(prompt, InvestigationPlan)
    print("\n===== PLANNER OUTPUT =====")
    print(plan.model_dump_json(indent=2))
    print("==========================\n")

    return {"plan": plan.model_dump_json(indent=2)}
