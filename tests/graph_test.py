
from app.agent.graph import build_investigation_graph


def test_graph_compiles():
    graph = build_investigation_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    graph = build_investigation_graph()

    expected_nodes = {
        "planner",
        "knowledge_retriever",
        "kql_generator",
        "kql_validator",
        "investigator",
        "evaluator",
    }

    actual_nodes = set(graph.get_graph().nodes)

    missing_nodes = expected_nodes - actual_nodes

    assert not missing_nodes, f"Missing nodes: {missing_nodes}"


if __name__ == "__main__":
    test_graph_compiles()
    test_graph_has_expected_nodes()
    print("Graph compilation and node checks passed.")
