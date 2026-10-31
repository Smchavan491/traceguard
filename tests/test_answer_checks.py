import pytest

from app.answer import Answer, check_citations


def test_valid_citation_passes():
    a = Answer(answer="x", cited_chunk_ids=["rb-1"], sufficient_evidence=True)
    check_citations(a, {"rb-1", "rb-2"})


def test_fake_citation_is_rejected():
    a = Answer(answer="x", cited_chunk_ids=["made-up"], sufficient_evidence=True)
    with pytest.raises(ValueError):
        check_citations(a, {"rb-1"})


def test_sufficient_evidence_without_citation_is_rejected():
    a = Answer(answer="x", cited_chunk_ids=[], sufficient_evidence=True)
    with pytest.raises(ValueError):
        check_citations(a, {"rb-1"})


def test_abstaining_is_allowed():
    a = Answer(answer="Not enough evidence.", cited_chunk_ids=[], sufficient_evidence=False)
    check_citations(a, {"rb-1"})