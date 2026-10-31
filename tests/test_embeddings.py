from typing import Any

import numpy as np
import pytest

from ingestion.embeddings import FastEmbedEmbeddings


class FakeTextEmbedding:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.passage_inputs: list[str] = []
        self.query_inputs: list[str] = []

    def passage_embed(self, texts: list[str]) -> list[np.ndarray[Any, Any]]:
        self.passage_inputs.extend(texts)
        return [np.zeros(384, dtype=np.float32) for _ in texts]

    def query_embed(self, query: str) -> list[np.ndarray[Any, Any]]:
        self.query_inputs.append(query)
        return [np.ones(384, dtype=np.float32)]


def test_langchain_wrapper_uses_passage_and_query_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_models: list[FakeTextEmbedding] = []

    def fake_model(model_name: str) -> FakeTextEmbedding:
        model = FakeTextEmbedding(model_name)
        created_models.append(model)
        return model

    monkeypatch.setattr("ingestion.embeddings.TextEmbedding", fake_model)
    embeddings = FastEmbedEmbeddings()

    document_vectors = embeddings.embed_documents(["first", "second"])
    query_vector = embeddings.embed_query("question")

    assert created_models[0].model_name == "BAAI/bge-small-en-v1.5"
    assert created_models[0].passage_inputs == ["first", "second"]
    assert created_models[0].query_inputs == ["question"]
    assert len(document_vectors) == 2
    assert all(len(vector) == 384 for vector in document_vectors)
    assert len(query_vector) == 384
