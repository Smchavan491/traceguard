from dataclasses import dataclass
import psycopg
from langchain_core.embeddings import Embeddings
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import settings
from ingestion.embeddings import FastEmbedEmbeddings

SEARCH_SQL = """
SELECT id, runbook, section, text, 1 - (embedding <=> %s) AS score
FROM runbook_chunks
ORDER BY embedding <=> %s
LIMIT %s
"""


@dataclass(frozen=True)
class RunbookSearchResult:
    chunk_id: str
    runbook: str
    section: str
    text: str
    score: float


def search_runbooks(
    query: str,
    k: int,
    *,
    embeddings: Embeddings | None = None,
) -> list[RunbookSearchResult]:
    """Rank by cosine similarity: 1 minus pgvector cosine distance; higher is better."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if k < 1:
        raise ValueError("k must be at least 1")

    embedding_model = embeddings if embeddings is not None else FastEmbedEmbeddings()
    query_vector = embedding_model.embed_query(query)
    if len(query_vector) != 384:
        raise ValueError("The query embedding must have 384 dimensions")

    with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                SEARCH_SQL,
                (Vector(query_vector), Vector(query_vector), k),
            )
            rows = cursor.fetchall()

    return [
        RunbookSearchResult(
            chunk_id=row[0],
            runbook=row[1],
            section=row[2],
            text=row[3],
            score=float(row[4]),
        )
        for row in rows
    ]
