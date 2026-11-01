import pytest

from app.answer import parse_answer


def test_plain_json():
    raw = '{"answer": "x", "cited_chunk_ids": ["rb-1"], "sufficient_evidence": true}'
    assert parse_answer(raw).cited_chunk_ids == ["rb-1"]


def test_fenced_json():
    raw = '```json\n{"answer": "x", "cited_chunk_ids": [], "sufficient_evidence": false}\n```'
    assert parse_answer(raw).sufficient_evidence is False


def test_sentence_around_json():
    raw = 'Sure! {"answer": "x", "cited_chunk_ids": [], "sufficient_evidence": false} Hope that helps!'
    assert parse_answer(raw).answer == "x"


def test_no_json_is_rejected():
    with pytest.raises(ValueError):
        parse_answer("Sure! Here is my answer.")


def test_missing_boxes_are_rejected():
    with pytest.raises(ValueError):
        parse_answer('{"answer": "x"}')