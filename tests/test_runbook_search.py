from unittest.mock import MagicMock

import numpy as np
import pytest
from langchain_core.embeddings import Embeddings

from tools.runbook_search import search_runbooks


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]

    def embed_query(self, query: str) -> list[float]:
        assert query == "database connections are exhausted"
        return np.zeros(384, dtype=np.float32).tolist()


def test_search_returns_cosine_similarity_and_chunk_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        ("rb-pool-main-001-a1", "pool", "Symptoms", "Pool requests time out.", 0.91),
        (
            "rb-timeout-main-001-b2",
            "timeout",
            "Symptoms",
            "Upstream requests time out.",
            0.62,
        ),
    ]
    monkeypatch.setattr(
        "tools.runbook_search.psycopg.connect",
        lambda *args, **kwargs: connection,
    )
    monkeypatch.setattr("tools.runbook_search.register_vector", lambda _: None)

    results = search_runbooks(
        "database connections are exhausted",
        k=2,
        embeddings=FakeEmbeddings(),
    )

    assert [result.score for result in results] == [0.91, 0.62]
    assert results[0].chunk_id == "rb-pool-main-001-a1"
    assert results[0].text == "Pool requests time out."
    executed_sql = cursor.execute.call_args.args[0]
    assert "1 - (embedding <=> %s) AS score" in executed_sql
    assert "ORDER BY embedding <=> %s" in executed_sql


def test_search_rejects_empty_query_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect = MagicMock()
    monkeypatch.setattr("tools.runbook_search.psycopg.connect", connect)

    try:
        search_runbooks("   ", k=2)
    except ValueError as error:
        assert str(error) == "query must not be empty"
    else:
        raise AssertionError("Expected an empty query to be rejected")

    connect.assert_not_called()
