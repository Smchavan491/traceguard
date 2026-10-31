from uuid import uuid4

import psycopg
import pytest
from langchain_core.embeddings import Embeddings

from app.config import settings
from ingestion.runbook_chunks import RunbookChunk
from ingestion.runbook_index import ingest_chunks
from tools.runbook_search import search_runbooks


class FixedEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector() for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector()

    @staticmethod
    def _vector() -> list[float]:
        return [1.0] + [0.0] * 383


@pytest.mark.postgres
def test_postgres_ingest_then_search_cleans_up_its_chunk() -> None:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as error:
        pytest.skip(f"PostgreSQL is unreachable: {error}")

    unique_id = uuid4().hex
    chunk = RunbookChunk(
        chunk_id=f"test-postgres-{unique_id}",
        runbook=f"pytest-{unique_id}",
        section="Integration test",
        text=f"Unique integration test runbook phrase {unique_id}.",
    )
    embeddings = FixedEmbeddings()
    ingested = False

    try:
        assert ingest_chunks([chunk], embeddings=embeddings) == 1
        ingested = True

        results = search_runbooks(
            f"Unique integration test runbook phrase {unique_id}.",
            k=100,
            embeddings=embeddings,
        )

        matching = [result for result in results if result.chunk_id == chunk.chunk_id]
        assert len(matching) == 1
        assert matching[0].text == chunk.text
        assert matching[0].score == pytest.approx(1.0)
    finally:
        if ingested:
            with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM runbook_chunks WHERE id = %s",
                        (chunk.chunk_id,),
                    )
