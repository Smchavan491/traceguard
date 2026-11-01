import pytest

from app.answer import parse_answer


def test_plain_json_is_parsed():
    raw = '{"answer": "x", "cited_chunk_ids": ["rb-1"], "sufficient_evidence": true}'
    assert parse_answer(raw).cited_chunk_ids == ["rb-1"]


def test_fenced_json_is_parsed():
    raw = '```json\n{"answer": "x", "cited_chunk_ids": [], "sufficient_evidence": false}\n```'
    assert parse_answer(raw).sufficient_evidence is False


def test_not_json_is_rejected():
    with pytest.raises(ValueError):
        parse_answer("Sure! Here is my answer.")


def test_wrong_shape_is_rejected():
    with pytest.raises(ValueError):
        parse_answer('{"answer": "x"}')