
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.evaluator import evaluator_node
from app.agent.nodes.investigator import investigator_node
from app.agent.nodes.knowledge_retriever import knowledge_retriever_node
from app.agent.nodes.kql_generator import kql_generator_node
from app.agent.nodes.kql_validator import kql_validator_node
from app.agent.nodes.outcomes import (
    mark_completed_node,
    mark_failed_node,
    mark_incomplete_node,
    mark_kql_exhausted_node,
)
from app.agent.nodes.planner import planner_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.tool_selector import tool_selector_node
from app.agent.state import InvestigationState


MAX_KQL_CORRECTION_ATTEMPTS = 1
DEFAULT_MAX_INVESTIGATION_STEPS = 5


def route_after_tool_selection(state: InvestigationState) -> str:
    """Decide whether to execute tools or finish the investigation."""

    if state.get("execution_complete", False):
        return "completed"

    if state.get("tool_calls"):
        return "execute_tools"

    # No valid tool calls and no completion decision.
    return "incomplete"


def route_after_tool_execution(state: InvestigationState) -> str:
    """Route pending graph capabilities to their workflows."""

    pending_capabilities = state.get("pending_capabilities", [])

    if "sentinel_investigation" in pending_capabilities:
        return "sentinel_investigation"

    return "select_again"


def route_after_kql_validation(state: InvestigationState) -> str:
    if not state.get("query", "").strip():
        return "kql_exhausted"

    if state.get("kql_valid", False):
        return "investigator"

    if (
        state.get("kql_correction_attempts", 0)
        < MAX_KQL_CORRECTION_ATTEMPTS
    ):
        return "retry"

    return "kql_exhausted"


def route_after_evaluation(state: InvestigationState) -> str:
    if state.get("investigation_status") == "failed":
        return "failed"

    if not state.get("needs_more_investigation", False):
        return "completed"

    max_steps = state.get(
        "max_investigation_steps",
        DEFAULT_MAX_INVESTIGATION_STEPS,
    )
    attempts = state.get("investigation_attempts", 0)

    if attempts >= max_steps:
        return "incomplete"

    return "select_again"


def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    # Existing investigation nodes
    graph.add_node("knowledge_retriever", knowledge_retriever_node)
    graph.add_node("planner", planner_node)
    graph.add_node("kql_generator", kql_generator_node)
    graph.add_node("kql_validator", kql_validator_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("evaluator", evaluator_node)

    # Dynamic tool nodes
    graph.add_node("tool_selector", tool_selector_node)
    graph.add_node("tool_executor", tool_executor_node)

    # Outcome nodes
    graph.add_node("mark_completed", mark_completed_node)
    graph.add_node("mark_incomplete", mark_incomplete_node)
    graph.add_node("mark_failed", mark_failed_node)
    graph.add_node("mark_kql_exhausted", mark_kql_exhausted_node)

    # Initial workflow
    graph.add_edge(START, "knowledge_retriever")
    graph.add_edge("knowledge_retriever", "planner")
    graph.add_edge("planner", "tool_selector")

    # Dynamic tool selection
    graph.add_conditional_edges(
        "tool_selector",
        route_after_tool_selection,
        {
            "execute_tools": "tool_executor",
            "completed": "mark_completed",
            "incomplete": "mark_incomplete",
        },
    )

    # Tool execution and capability routing
    graph.add_conditional_edges(
        "tool_executor",
        route_after_tool_execution,
        {
            "sentinel_investigation": "kql_generator",
            "select_again": "tool_selector",
        },
    )

    # Existing KQL generation and validation pipeline
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

    # Investigation and evaluation
    graph.add_edge("investigator", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "select_again": "tool_selector",
            "completed": "mark_completed",
            "incomplete": "mark_incomplete",
            "failed": "mark_failed",
        },
    )

    # Terminal outcomes
    graph.add_edge("mark_completed", END)
    graph.add_edge("mark_incomplete", END)
    graph.add_edge("mark_failed", END)
    graph.add_edge("mark_kql_exhausted", END)

    return graph.compile()
