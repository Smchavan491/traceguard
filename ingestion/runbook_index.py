from collections.abc import Sequence
from typing import Any

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from langchain_core.embeddings import Embeddings

from app.config import settings
from ingestion.embeddings import FastEmbedEmbeddings
from ingestion.runbook_chunks import RunbookChunk

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS runbook_chunks (
    id TEXT PRIMARY KEY,
    runbook TEXT NOT NULL,
    section TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384) NOT NULL
)
"""

UPSERT_CHUNK_SQL = """
INSERT INTO runbook_chunks (id, runbook, section, text, embedding)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    runbook = EXCLUDED.runbook,
    section = EXCLUDED.section,
    text = EXCLUDED.text,
    embedding = EXCLUDED.embedding
"""


def ensure_runbook_table(connection: Any) -> None:
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(connection)
    connection.execute(CREATE_TABLE_SQL)


def ingest_chunks(
    chunks: Sequence[RunbookChunk],
    embeddings: Embeddings | None = None,
) -> int:
    """Create the table and idempotently insert or update runbook chunks."""
    if not chunks:
        return 0
    embedding_model = embeddings if embeddings is not None else FastEmbedEmbeddings()
    vectors = embedding_model.embed_documents([chunk.text for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError(
            "The embedding model returned a different number of vectors than chunks"
        )
    if any(len(vector) != 384 for vector in vectors):
        raise ValueError("Every runbook embedding must have 384 dimensions")

    with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
        ensure_runbook_table(connection)
        with connection.cursor() as cursor:
            cursor.executemany(
                UPSERT_CHUNK_SQL,
                [
                    (
                        chunk.chunk_id,
                        chunk.runbook,
                        chunk.section,
                        chunk.text,
                        Vector(vector),
                    )
                    for chunk, vector in zip(chunks, vectors, strict=True)
                ],
            )
    return len(chunks)
