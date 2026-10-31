from pathlib import Path

from ingestion.runbook_chunks import load_runbook_chunks
from ingestion.runbook_index import ingest_chunks

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_DIR = ROOT / "data" / "runbooks"


def main() -> None:
    chunks = load_runbook_chunks(RUNBOOK_DIR)
    count = ingest_chunks(chunks)
    print(f"Ingested {count} runbook chunks into runbook_chunks.")


if __name__ == "__main__":
    main()
