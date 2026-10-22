
from functools import lru_cache
from pathlib import Path
import hashlib
import re

import chromadb
from sentence_transformers import SentenceTransformer


# Resolve paths from the project root, not the terminal's current directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = chroma_client.get_or_create_collection(
    name="siem_knowledge_cosine_chunks",
    metadata={"hnsw:space": "cosine"},
)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once per Python process."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def chunk_markdown(text: str) -> list[dict[str, str]]:
    """Split the Markdown document into sections headed by ##."""
    sections = re.split(r"(?m)^##\s+", text)
    chunks = []

    for section in sections:
        section = section.strip()

        if not section or section.startswith("# Microsoft Sentinel Tables"):
            continue

        lines = section.splitlines()
        table_name = lines[0].strip()
        document = f"## {section}"

        chunks.append({
            "table": table_name,
            "document": document,
            "content_hash": hashlib.sha256(
                document.encode("utf-8")
            ).hexdigest(),
        })

    return chunks


def ingest_knowledge(file_path: Path) -> dict[str, int]:
    """Embed new or changed sections and remove stale sections."""
    source = file_path.relative_to(PROJECT_ROOT).as_posix()
    text = file_path.read_text(encoding="utf-8")
    chunks = chunk_markdown(text)

    existing = collection.get(
        where={"source": source},
        include=["metadatas"],
    )

    existing_metadata = dict(
        zip(existing["ids"], existing["metadatas"])
    )

    current_ids = set()
    embedded_count = 0

    for chunk in chunks:
        record_id = f"{source}:{chunk['table']}"
        current_ids.add(record_id)

        previous_metadata = existing_metadata.get(record_id, {})

        # Skip embedding if the document has not changed.
        if (
            previous_metadata
            and previous_metadata.get("content_hash")
            == chunk["content_hash"]
        ):
            continue

        embedding = get_embedding_model().encode(
            chunk["document"]
        ).tolist()

        collection.upsert(
            ids=[record_id],
            documents=[chunk["document"]],
            embeddings=[embedding],
            metadatas=[{
                "source": source,
                "type": "table_schema",
                "table": chunk["table"],
                "content_hash": chunk["content_hash"],
            }],
        )

        embedded_count += 1

    # Remove records for sections deleted from the source document.
    stale_ids = set(existing["ids"]) - current_ids

    if stale_ids:
        collection.delete(ids=list(stale_ids))

    return {
        "sections_found": len(chunks),
        "sections_embedded_or_updated": embedded_count,
        "stale_sections_removed": len(stale_ids),
    }


def search_knowledge(
    query: str,
    n_results: int = 3,
) -> list[dict]:
    """Embed a search query and retrieve matching knowledge."""
    if not query.strip():
        return []

    if collection.count() == 0:
        return []

    query_embedding = get_embedding_model().encode(
        query
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
    )

    return [
        {
            "document": document,
            "metadata": metadata,
            "distance": distance,
        }
        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
