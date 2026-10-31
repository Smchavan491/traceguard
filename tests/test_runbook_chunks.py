from pathlib import Path

import pytest

from ingestion.runbook_chunks import split_runbook


def test_runbook_chunks_have_stable_ids_and_section_metadata(tmp_path: Path) -> None:
    runbook = tmp_path / "connection-pool.md"
    runbook.write_text(
        "# Connection Pool\n\n"
        + ("Check database connections and request timeouts. " * 20),
        encoding="utf-8",
    )

    first = split_runbook(runbook, chunk_size=100, chunk_overlap=10)
    second = split_runbook(runbook, chunk_size=100, chunk_overlap=10)

    assert first == second
    assert len(first) > 1
    assert all(chunk.runbook == "connection-pool" for chunk in first)
    assert all(chunk.section == "Connection Pool" for chunk in first)
    assert all(
        chunk.chunk_id.startswith("rb-connection-pool-connection-pool-")
        for chunk in first
    )


def test_runbook_chunk_overlap_must_be_smaller_than_chunk_size(tmp_path: Path) -> None:
    runbook = tmp_path / "invalid.md"
    runbook.write_text("# Heading\n\nSome text.", encoding="utf-8")

    with pytest.raises(ValueError, match="smaller than chunk_size"):
        split_runbook(runbook, chunk_size=10, chunk_overlap=10)
