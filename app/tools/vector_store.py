
from functools import lru_cache
from pathlib import Path
import hashlib
import re

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"

chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

collection = chroma_client.get_or_create_collection(
    name="siem_knowledge_cosine_chunks",
    metadata={"hnsw:space": "cosine"},
)

@lru_cache(maxsize=128)
def _embed_query(query: str) -> tuple[float, ...]:
    embedding = get_embedding_model().encode(
        query.strip()
    )
    return tuple(float(value) for value in embedding)

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once per Python process."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def chunk_markdown(text: str, source_type: str) -> list[dict[str, str]]:
    """Split Markdown into retrievable sections."""
    sections = re.split(r"(?m)^##\s+", text)
    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        lines = section.splitlines()
        title = lines[0].strip()

        # Skip a top-level document title if present.
        if title.startswith("# "):
            continue

        document = f"## {section}"

        if source_type == "table_schema":
            # Existing schema documents use the section heading as table name.
            if title.startswith("Microsoft Sentinel Tables"):
                continue

            chunks.append({
                "title": title,
                "document": document,
                "type": "table_schema",
                "content_hash": hashlib.sha256(
                    document.encode("utf-8")
                ).hexdigest(),
            })
        else:
            chunks.append({
                "title": title,
                "document": document,
                "type": "runbook",
                "content_hash": hashlib.sha256(
                    document.encode("utf-8")
                ).hexdigest(),
            })

    return chunks


def ingest_knowledge(file_path: Path) -> dict[str, int]:
    """Embed changed sections and remove stale sections for one source."""
    file_path = file_path.resolve()
    source = file_path.relative_to(PROJECT_ROOT).as_posix()

    source_type = (
        "table_schema"
        if file_path.name == "tables.md"
        else "runbook"
    )

    text = file_path.read_text(encoding="utf-8")
    chunks = chunk_markdown(text, source_type)

    existing = collection.get(
        where={"source": source},
        include=["metadatas"],
    )

    existing_metadata = dict(zip(existing["ids"], existing["metadatas"]))

    current_ids = set()
    embedded_count = 0

    for chunk in chunks:
        record_id = f"{source}:{chunk['title']}"
        current_ids.add(record_id)

        previous_metadata = existing_metadata.get(record_id, {})

        if (
            previous_metadata
            and previous_metadata.get("content_hash")
            == chunk["content_hash"]
            and previous_metadata.get("type") == chunk["type"]
        ):
            continue

        embedding = get_embedding_model().encode(
            chunk["document"]
        ).tolist()

        metadata = {
            "source": source,
            "type": chunk["type"],
            "title": chunk["title"],
            "content_hash": chunk["content_hash"],
        }

        if chunk["type"] == "table_schema":
            metadata["table"] = chunk["title"]

        collection.upsert(
            ids=[record_id],
            documents=[chunk["document"]],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        embedded_count += 1

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
    source_type: str | None = None,
) -> list[dict]:
    """Retrieve relevant knowledge, optionally filtered by document type."""
    if not query.strip() or collection.count() == 0:
        return []

    query_embedding = list(_embed_query(query))
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count()),
    }

    if source_type:
        query_args["where"] = {"type": source_type}

    results = collection.query(**query_args)

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
