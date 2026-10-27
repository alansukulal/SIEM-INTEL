
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
from app.agent.state import InvestigationState


MAX_KQL_CORRECTION_ATTEMPTS = 1



def route_after_kql_validation(state: InvestigationState) -> str:
    # Stop immediately if the generator could not produce a query.
    if not state.get("query", "").strip():
        return "kql_exhausted"

    if state["kql_valid"]:
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

    max_steps = state.get("max_investigation_steps", 10)
    attempts = state.get("investigation_attempts", 0)

    if attempts >= max_steps:
        return "incomplete"

    return "retry"


def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("planner", planner_node)
    graph.add_node("knowledge_retriever", knowledge_retriever_node)
    graph.add_node("kql_generator", kql_generator_node)
    graph.add_node("kql_validator", kql_validator_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("evaluator", evaluator_node)

    graph.add_node("mark_completed", mark_completed_node)
    graph.add_node("mark_incomplete", mark_incomplete_node)
    graph.add_node("mark_failed", mark_failed_node)
    graph.add_node("mark_kql_exhausted", mark_kql_exhausted_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "knowledge_retriever")
    graph.add_edge("knowledge_retriever", "kql_generator")
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

    graph.add_edge("investigator", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "completed": "mark_completed",
            "incomplete": "mark_incomplete",
            "failed": "mark_failed",
            "retry": "kql_generator",
        },
    )

    graph.add_edge("mark_completed", END)
    graph.add_edge("mark_incomplete", END)
    graph.add_edge("mark_failed", END)
    graph.add_edge("mark_kql_exhausted", END)

    return graph.compile()
