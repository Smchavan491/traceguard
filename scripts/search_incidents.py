from pathlib import Path

from app.incident_loader import load_incident_for_agent
from app.config import settings
from ingestion.embeddings import FastEmbedEmbeddings
from tools.runbook_search import search_runbooks

ROOT = Path(__file__).resolve().parents[1]
INCIDENT_DIR = ROOT / "data" / "incidents"


def main() -> None:
    incident_dirs = sorted(path for path in INCIDENT_DIR.iterdir() if path.is_dir())
    embeddings = FastEmbedEmbeddings()
    for incident_dir in incident_dirs:
        incident_data = load_incident_for_agent(incident_dir)
        results = search_runbooks(
            incident_data.incident.symptom,
            settings.rag_top_k,
            embeddings=embeddings,
        )
        print(f"{incident_data.incident.incident_id}: {incident_data.incident.symptom}")
        for rank, result in enumerate(results, start=1):
            print(f"  {rank}. {result.chunk_id} score={result.score:.6f}")
        if len(results) >= 2:
            gap = results[0].score - results[1].score
            print(f"  top1_top2_score_gap={gap:.6f}")
        else:
            print("  top1_top2_score_gap=unavailable (fewer than two results)")


if __name__ == "__main__":
    main()
