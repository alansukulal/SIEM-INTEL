
from app.tools.knowledge_tools import knowledge_search


def test_knowledge_search():
    results = knowledge_search(
        query="Sentinel log ingestion troubleshooting",
        source_type="runbook",
        limit=3,
    )

    print("Results returned:", len(results))

    for result in results:
        print("Document:", result["document"][:200])
        print("Metadata:", result["metadata"])


if __name__ == "__main__":
    test_knowledge_search()
