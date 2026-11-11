
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.evaluator import evaluator_node
from app.agent.nodes.investigator import investigator_node
from app.agent.nodes.knowledge_retriever import knowledge_retriever_node
from app.agent.nodes.kql_generator import kql_generator_node
from app.agent.nodes.kql_validator import kql_validator_node
from app.agent.nodes.outcomes import (
    mark_completed_node,
    mark_incomplete_node,
    mark_kql_exhausted_node,
)
from app.agent.nodes.planner import planner_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.tool_selector import tool_selector_node
from app.agent.state import InvestigationState


MAX_KQL_CORRECTION_ATTEMPTS = 1
DEFAULT_MAX_TOOL_EXECUTION_ATTEMPTS = 10
DEFAULT_MAX_INVESTIGATION_STEPS = 3


def route_after_tool_selection(state: InvestigationState) -> str:
    """
    Route selected tools for execution.

    The selector cannot independently declare an investigation
    successful. Its completion decision is sent to the evaluator.
    """

    tool_calls = state.get("tool_calls", [])

    tool_attempts = state.get("tool_execution_attempts", 0)
    max_tool_attempts = state.get(
        "max_tool_execution_attempts",
        DEFAULT_MAX_TOOL_EXECUTION_ATTEMPTS,
    )

    if tool_calls and tool_attempts < max_tool_attempts:
        return "execute_tools"

    # Evaluate existing evidence even when the selector has no
    # more tools to execute or the execution budget is exhausted.
    return "evaluate"


def route_after_tool_execution(state: InvestigationState) -> str:
    pending_capabilities = state.get("pending_capabilities", [])

    if "sentinel_investigation" in pending_capabilities:
        investigation_attempts = state.get(
            "investigation_attempts", 0
        )
        max_investigation_steps = state.get(
            "max_investigation_steps",
            DEFAULT_MAX_INVESTIGATION_STEPS,
        )

        if investigation_attempts < max_investigation_steps:
            return "sentinel_investigation"

        return "evaluate"

    if state.get("tool_batch_complete") and (
        state.get("tool_results") or state.get("tool_errors")
    ):
        return "evaluate"

    return "select_again"


def route_after_kql_validation(state: InvestigationState) -> str:
    """Validate generated KQL and control correction attempts."""

    query = state.get("query") or ""

    if not isinstance(query, str) or not query.strip():
        return "kql_exhausted"

    if state.get("kql_valid", False):
        return "investigator"

    correction_attempts = state.get(
        "kql_correction_attempts",
        0,
    )

    if correction_attempts <= MAX_KQL_CORRECTION_ATTEMPTS:
        return "retry"

    return "kql_exhausted"


def route_after_evaluation(state: InvestigationState) -> str:
    """
    Route based on whether the objective was answered,
    not merely whether the agent has stopped investigating.
    """

    if state.get("investigation_complete", False):
        return "completed"

    if state.get("needs_more_investigation", False):
        tool_attempts = state.get(
            "tool_execution_attempts", 0
        )
        max_tool_attempts = state.get(
            "max_tool_execution_attempts",
            DEFAULT_MAX_TOOL_EXECUTION_ATTEMPTS,
        )

        if tool_attempts < max_tool_attempts:
            return "select_again"

    return "incomplete"


def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    # Core investigation nodes.
    graph.add_node(
        "knowledge_retriever",
        knowledge_retriever_node,
    )

    graph.add_node("planner", planner_node)

    graph.add_node("kql_generator", kql_generator_node)
    graph.add_node("kql_validator", kql_validator_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("evaluator", evaluator_node)

    # Dynamic tool orchestration.
    graph.add_node("tool_selector", tool_selector_node)
    graph.add_node("tool_executor", tool_executor_node)

    # Outcome nodes.
    graph.add_node("mark_completed", mark_completed_node)
    graph.add_node("mark_incomplete", mark_incomplete_node)
    graph.add_node("mark_kql_exhausted", mark_kql_exhausted_node)

    # Initial workflow.
    graph.add_edge(START, "knowledge_retriever")
    graph.add_edge("knowledge_retriever", "planner")
    graph.add_edge("planner", "tool_selector")

    # Tool selection.
    graph.add_conditional_edges(
        "tool_selector",
        route_after_tool_selection,
        {
            "execute_tools": "tool_executor",
            "evaluate": "evaluator",
        },
    )

    # Tool execution.
    graph.add_conditional_edges(
        "tool_executor",
        route_after_tool_execution,
        {
            "sentinel_investigation": "kql_generator",
            "select_again": "tool_selector",
            "evaluate": "evaluator",
        },
    )

    # Sentinel KQL workflow.
    graph.add_edge("kql_generator", "kql_validator")

    graph.add_conditional_edges(
        "kql_validator",
        route_after_kql_validation,
        {
            "investigator": "investigator",
            "retry": "kql_generator",
            "kql_exhausted": "mark_kql_exhausted",
        },
    )

    # Investigation and evaluation.
    graph.add_edge("investigator", "evaluator")
    graph.add_edge("mark_kql_exhausted", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "select_again": "tool_selector",
            "completed": "mark_completed",
            "incomplete": "mark_incomplete",
        },
    )

    # Terminal outcomes.
    graph.add_edge("mark_completed", END)
    graph.add_edge("mark_incomplete", END)

    return graph.compile()


investigation_graph = build_investigation_graph()
