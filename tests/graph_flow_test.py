
from app.agent.graph import build_investigation_graph


def test_graph_compiles():
    graph = build_investigation_graph()
    assert graph is not None
    print("Investigation graph compiled successfully.")


if __name__ == "__main__":
    test_graph_compiles()
