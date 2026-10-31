from unittest.mock import MagicMock

import pytest
from langchain_core.embeddings import Embeddings

from ingestion.runbook_chunks import RunbookChunk
from ingestion.runbook_index import CREATE_TABLE_SQL, UPSERT_CHUNK_SQL, ingest_chunks


class FakeEmbeddings(Embeddings):
    def embed_query(self, text: str) -> list[float]:
        return [0.0] * 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        assert texts == ["A synthetic runbook chunk."]
        return [[0.0] * 384]


def test_ingestion_upserts_chunks_without_ann_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()
    monkeypatch.setattr(
        "ingestion.runbook_index.psycopg.connect",
        lambda *args, **kwargs: connection,
    )
    monkeypatch.setattr("ingestion.runbook_index.register_vector", lambda _: None)
    chunk = RunbookChunk(
        chunk_id="rb-sample-section-001-a1b2c3",
        runbook="sample",
        section="Section",
        text="A synthetic runbook chunk.",
    )

    count = ingest_chunks([chunk], embeddings=FakeEmbeddings())

    assert count == 1
    statements = [
        call.args[0]
        for call in connection.__enter__.return_value.execute.call_args_list
    ]
    assert "CREATE EXTENSION IF NOT EXISTS vector" in statements
    assert CREATE_TABLE_SQL in statements
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    upsert_call = cursor.executemany.call_args
    assert upsert_call.args[0] == UPSERT_CHUNK_SQL
    assert "ON CONFLICT (id) DO UPDATE" in UPSERT_CHUNK_SQL
    assert "CREATE INDEX" not in CREATE_TABLE_SQL
