
from langgraph.graph import END, START, StateGraph

from app.agent.nodes.evaluator import evaluator_node
from app.agent.nodes.investigator import investigator_node
from app.agent.nodes.knowledge_retriever import knowledge_retriever_node
from app.agent.nodes.kql_generator import kql_generator_node
from app.agent.nodes.kql_validator import kql_validator_node
from app.agent.nodes.planner import planner_node
from app.agent.state import InvestigationState


def route_after_kql_validation(
    state: InvestigationState,
) -> str:
    if state["kql_valid"]:
        return "investigator"

    if state["kql_attempts"] < 3:
        return "retry"

    return "end"



def route_after_evaluation(
    state: InvestigationState,
) -> str:
    # Never retry if Sentinel execution failed.
    if state.get("investigation_status") == "failed":
        return "end"

    # Stop if the evaluator says the evidence is sufficient.
    if not state["needs_more_investigation"]:
        return "end"

    # Enforce both retry limits.
    if (
        state["investigation_attempts"] >= 3
        or state["kql_attempts"] >= 3
    ):
        return "end"

    return "retry"



def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("planner", planner_node)
    graph.add_node("knowledge_retriever", knowledge_retriever_node)
    graph.add_node("kql_generator", kql_generator_node)
    graph.add_node("kql_validator", kql_validator_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("evaluator", evaluator_node)

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
            "end": END,
        },
    )

    graph.add_edge("investigator", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {
            "retry": "kql_generator",
            "end": END,
        },
    )

    return graph.compile()
