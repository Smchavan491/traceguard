"""Answer model and citation checks. No LLM calls in this file."""
from pydantic import BaseModel


class Answer(BaseModel):
    answer: str
    cited_chunk_ids: list[str]
    sufficient_evidence: bool


def check_citations(answer: Answer, retrieved_ids: set[str]) -> None:
    """Raise ValueError if the answer cites something we never retrieved."""
    unknown = [c for c in answer.cited_chunk_ids if c not in retrieved_ids]
    if unknown:
        raise ValueError(f"Cited chunk IDs that were not retrieved: {unknown}")
    if answer.sufficient_evidence and not answer.cited_chunk_ids:
        raise ValueError("Claims sufficient evidence but cites nothing")