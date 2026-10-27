
from pathlib import Path

from app.tools.vector_store import ingest_knowledge


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge" / "sentinel"


def main() -> None:
    knowledge_files = sorted(KNOWLEDGE_DIR.rglob("*.md"))

    if not knowledge_files:
        print(f"No Markdown knowledge files found in: {KNOWLEDGE_DIR}")
        return

    total_sections = 0
    total_embedded = 0
    total_stale_removed = 0

    print(f"Found {len(knowledge_files)} knowledge file(s).\n")

    for file_path in knowledge_files:
        print(f"Processing: {file_path.relative_to(PROJECT_ROOT)}")

        result = ingest_knowledge(file_path)

        total_sections += result["sections_found"]
        total_embedded += result["sections_embedded_or_updated"]
        total_stale_removed += result["stale_sections_removed"]

        print(f"  Sections found: {result['sections_found']}")
        print(
            "  Sections embedded or updated: "
            f"{result['sections_embedded_or_updated']}"
        )
        print(
            f"  Stale sections removed: "
            f"{result['stale_sections_removed']}\n"
        )

    print("Knowledge ingestion completed.")
    print(f"Total sections found: {total_sections}")
    print(f"Total sections embedded or updated: {total_embedded}")
    print(f"Total stale sections removed: {total_stale_removed}")


if __name__ == "__main__":
    main()
