
from app.tools.vector_store import ingest_knowledge
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

knowledge_file = (
    PROJECT_ROOT / "knowledge" / "sentinel" / "tables.md"
)

result = ingest_knowledge(knowledge_file)

print("Knowledge ingestion completed.")
print(f"Sections found: {result['sections_found']}")
print(
    "Sections embedded or updated: "
    f"{result['sections_embedded_or_updated']}"
)
print(
    "Stale sections removed: "
    f"{result['stale_sections_removed']}"
)
