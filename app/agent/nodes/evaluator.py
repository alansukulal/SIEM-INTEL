
import json
import logging

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.evaluation import EvaluationResult

logger = logging.getLogger(__name__)


def _format_context(value, limit=4000):
    """Safely format tool context while controlling prompt size."""
    try:
        return json.dumps(value, default=str)[:limit]
    except (TypeError, ValueError):
        return str(value)[:limit]


def _has_supporting_evidence(state: InvestigationState) -> bool:
    """
    Check whether the investigation has collected any evidence
    that could support a completion decision.

    This is a minimum evidence-presence check, not a semantic
    judgment that the evidence answers the objective.
    """

    # Current Sentinel evidence.
    evidence = state.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        return True

    # Historical successful Sentinel evidence.
    history = state.get("investigation_history", [])

    if isinstance(history, list):
        for item in history:
            if not isinstance(item, dict):
                continue

            if item.get("status") != "success":
                continue

            historical_evidence = item.get("evidence", [])

            if isinstance(historical_evidence, list) and historical_evidence:
                return True

    # Internal knowledge retrieval.
    knowledge = state.get("knowledge", [])
    if isinstance(knowledge, list) and knowledge:
        return True

    # Results returned by other investigation tools.
    tool_results = state.get("tool_results", [])
    if isinstance(tool_results, list) and tool_results:
        return True

    return False


def evaluator_node(state: InvestigationState) -> dict:
    evidence = state.get("evidence", [])
    history = state.get("investigation_history", [])

    tool_results = state.get("tool_results", [])
    tool_errors = state.get("tool_errors", [])
    tool_calls = state.get("tool_calls", [])

    investigation_attempts = state.get(
        "investigation_attempts", 0
    )
    max_investigation_steps = state.get(
        "max_investigation_steps", 5
    )

    tool_attempts = state.get(
        "tool_execution_attempts", 0
    )
    max_tool_attempts = state.get(
        "max_tool_execution_attempts", 10
    )

    sentinel_budget_available = (
        investigation_attempts < max_investigation_steps
    )

    tool_budget_available = (
        tool_attempts < max_tool_attempts
    )

    # Parse the structured investigation plan.
    raw_plan = state.get("plan", "")

    try:
        plan = json.loads(raw_plan) if raw_plan else {}
    except (json.JSONDecodeError, TypeError):
        plan = {"objective": raw_plan}

    plan_context = _format_context(plan, 2500)

    evidence_context = _format_context(
        evidence[-5:] if isinstance(evidence, list) else evidence,
        3000,
    )

    tool_results_context = _format_context(
        tool_results[-10:],
        5000,
    )

    tool_errors_context = _format_context(
        tool_errors[-5:],
        2000,
    )

    tool_calls_context = _format_context(
        tool_calls[-10:],
        2000,
    )

    
    history_items = []

    for item in history[-5:]:
        if not isinstance(item, dict):
            continue

        previous_evidence = item.get("evidence", [])
        status = item.get("status", "unknown")

        # Only successful Sentinel queries contribute historical evidence.
        if status != "success":
            previous_evidence = []

        history_items.append({
            "query": item.get("query", ""),
            "status": status,
            "evidence": (
                previous_evidence
                if isinstance(previous_evidence, list)
                else []
            ),
            "evidence_row_count": (
                len(previous_evidence)
                if isinstance(previous_evidence, list)
                else 0
            ),
            "error": item.get("error", ""),
        })

    history_context = _format_context(
        history_items,
        6000,
    )

    prompt = f"""
You are the investigation evaluator for SIEM-INTEL,
an agentic SIEM investigation platform.

Your responsibility is to evaluate all available evidence
against the original investigation objective.

ORIGINAL ALERT OR QUESTION:
{state.get("alert", "")}

SIEM:
{state.get("siem", "")}

INVESTIGATION PLAN:
{plan_context}

CURRENT FINDING:
{state.get("finding", "")}

LATEST KQL:
{state.get("query", "")}

LATEST SENTINEL STATUS:
{state.get("investigation_status", "unknown")}

LATEST INVESTIGATION ERROR:
{state.get("investigation_error", "")}

SENTINEL EVIDENCE:
{evidence_context}

RESULTS FROM ALL TOOLS:
{tool_results_context}

SELECTED TOOL CALLS:
{tool_calls_context}

TOOL EXECUTION ERRORS:
{tool_errors_context}

HISTORICAL SENTINEL INVESTIGATIONS:
{history_context}

IMPORTANT EVIDENCE RULES:
- Historical evidence from successful queries remains available.
- Historical evidence from failed queries must never be treated
  as collected evidence.
- Evaluate evidence from all successful queries, not just the
  latest query.
- A successful query with zero rows does not establish that
  the underlying issue is absent.
- Consider the query and its result together when interpreting
  historical evidence.
- Do not assume that older evidence represents current health.

SENTINEL INVESTIGATION BUDGET:
{investigation_attempts}/{max_investigation_steps}
Available: {sentinel_budget_available}

DIRECT TOOL EXECUTION BUDGET:
{tool_attempts}/{max_tool_attempts}
Available: {tool_budget_available}

EVALUATION RULES:

1. Evaluate the original objective, not just the latest tool result.

2. Consider evidence from:
   - Microsoft Sentinel investigations.
   - Internal knowledge search.
   - External web search.
   - Scraped documentation and webpages.

3. Distinguish verified facts, assumptions, and missing evidence.

4. A successful web search does not automatically mean
   the original investigation objective is answered.

5. Documentation explains expected behavior but does not
   independently prove the health of a customer's SIEM.

6. A failed Sentinel query does not prove an alert is true or false.

7. A failed tool does not invalidate evidence from successful tools.

8. If Sentinel fails, consider whether another capability
   can resolve the unanswered question.

9. If documentation is available but customer-specific evidence
   is missing, clearly identify that limitation.

10. Avoid repeating previous actions unless new evidence
    provides a valid reason.

11. Request further investigation only when a useful action
    can resolve an important unanswered question.

12. Set investigation_complete=True ONLY when sufficient
    evidence answers the original objective.

13. If the original objective remains unresolved, set
    investigation_complete=False, even if no further actions
    are available.

14. Set needs_more_investigation=True only when a useful
    additional investigation action is available.

15. If no useful action remains, set
    needs_more_investigation=False.

16. If the direct tool budget is exhausted, do not request
    additional direct tool executions.

17. If Sentinel's investigation budget is exhausted, do not
    request another Sentinel investigation. Other capabilities
    may still be useful if their budget is available.

18. Never claim a tool succeeded unless its result confirms it.

19. Findings must be concise, factual, and evidence-based.
20. Explicitly assess whether the collected evidence is relevant
    and sufficient to answer the original objective.

21. Set evidence_sufficient=True only when the evidence directly
    supports the conclusion. Evidence presence alone is insufficient.

22. Populate missing_evidence with the important missing or
    unverified evidence.

23. Documentation can support configuration and procedural
    questions, but cannot independently establish current
    customer-specific SIEM health.

24. If evidence_sufficient=False, investigation_complete
    MUST be False.

25. Explain your evidence decision in evidence_assessment.

IMPORTANT:
An investigation that stops is not automatically completed.
An investigation that runs out of tools is not automatically completed.
Only sufficient evidence can justify investigation_complete=True.

Return:
- finding
- investigation_complete
- needs_more_investigation
- next_investigation_reason
"""

    result: EvaluationResult = LLMClient().invoke_structured(
        prompt,
        EvaluationResult,
    )
    print("\n========== EVALUATOR RAW RESULT ==========")
    print(result.model_dump_json(indent=2))
    print("==========================================\n")
        

    # Enforce tool budgets in application code.
    
    # Enforce tool budgets in application code.
    needs_more_investigation = (
        result.needs_more_investigation
        and tool_budget_available
        and bool((result.next_investigation_reason or "").strip())
    )

    # Completion requires both model decisions to agree.
    investigation_complete = (
        result.investigation_complete
        and result.evidence_sufficient
        and not result.needs_more_investigation
    )

    # Reject unsupported completion.
    if result.investigation_complete and not result.evidence_sufficient:
        logger.warning(
            "Evaluator attempted completion with insufficient evidence: %s",
            result.evidence_assessment,
        )

    # Minimum evidence-presence safeguard.
    if investigation_complete and not _has_supporting_evidence(state):
        logger.warning(
            "Evaluator attempted completion without collected evidence."
        )
        investigation_complete = False

    # Reject conflicting completion and continuation decisions.
    if result.investigation_complete and result.needs_more_investigation:
        logger.warning(
            "Evaluator returned conflicting completion and "
            "continuation decisions."
        )
        investigation_complete = False

    next_reason = (
        result.next_investigation_reason
        if needs_more_investigation
        else ""
    )

    if result.needs_more_investigation and not tool_budget_available:
        logger.warning(
            "Investigation stopped because the direct tool "
            "execution budget was exhausted."
        )

    return {
        "finding": result.finding,
        "investigation_complete": investigation_complete,
        "needs_more_investigation": needs_more_investigation,
        "next_investigation_reason": next_reason,
        "evidence_sufficient": result.evidence_sufficient,
        "evidence_assessment": result.evidence_assessment,
        "missing_evidence": result.missing_evidence,
    }
