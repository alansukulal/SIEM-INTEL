
from app.tools.vector_store import search_knowledge

queries = [
    "Where can I investigate failed user sign-ins?",
    "How can I check whether Sentinel agents are sending heartbeats?",
    "Where can I investigate Windows security events?",
]

for query in queries:
    print(f"\nQUERY: {query}")

    results = search_knowledge(query, n_results=1)

    if not results:
        print("No knowledge found.")
        continue

    for result in results:
        print("Matched table:", result["metadata"]["table"])
        print("Distance:", round(result["distance"], 4))
        print("Document:", result["document"][:200])
