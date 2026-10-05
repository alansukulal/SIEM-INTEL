from langgraph.graph import END, START, StateGraph

from app.agent.nodes.evaluator import evaluator_node
from app.agent.nodes.investigator import investigator_node
from app.agent.nodes.planner import planner_node
from app.agent.state import InvestigationState


def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("planner", planner_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("evaluator", evaluator_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "investigator")
    graph.add_edge("investigator", "evaluator")
    graph.add_edge("evaluator", END)

    return graph.compile()