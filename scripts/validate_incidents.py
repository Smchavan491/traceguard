import json
from pathlib import Path

from app.schemas import DependencyMap, DeploymentEvent, GroundTruth, Incident, LogLine

ROOT = Path(__file__).resolve().parents[1]
INCIDENT_ROOT = ROOT / "data" / "incidents"


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_incident_folder(incident_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        incident = Incident.model_validate(_load_json(incident_dir / "incident.json"))
        logs = [LogLine.model_validate(item) for item in _load_json(incident_dir / "logs.json")]
        deployments = [
            DeploymentEvent.model_validate(item)
            for item in _load_json(incident_dir / "deployments.json")
        ]
        dependency_map = DependencyMap.model_validate(
            _load_json(incident_dir / "dependency_map.json")
        )
        ground_truth = GroundTruth.model_validate(
            _load_json(incident_dir / "ground_truth.json")
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"{incident_dir.name}: {error}"]

    if not 100 <= len(logs) <= 300:
        errors.append(f"{incident_dir.name}: expected 100-300 log lines, got {len(logs)}")
    if incident.incident_id != dependency_map.incident_id:
        errors.append(f"{incident_dir.name}: dependency map incident_id does not match")
    if incident.incident_id != ground_truth.incident_id:
        errors.append(f"{incident_dir.name}: ground truth incident_id does not match")

    log_ids = [line.log_id for line in logs]
    deployment_ids = [event.deployment_id for event in deployments]
    if len(log_ids) != len(set(log_ids)):
        errors.append(f"{incident_dir.name}: duplicate log IDs")
    if len(deployment_ids) != len(set(deployment_ids)):
        errors.append(f"{incident_dir.name}: duplicate deployment IDs")
    evidence_ids = set(log_ids) | set(deployment_ids)
    missing_ids = sorted(set(ground_truth.key_evidence_ids) - evidence_ids)
    if missing_ids:
        errors.append(f"{incident_dir.name}: key evidence IDs not found: {', '.join(missing_ids)}")

    return errors


def validate_dataset(incident_root: Path = INCIDENT_ROOT) -> list[str]:
    folders = sorted(path for path in incident_root.iterdir() if path.is_dir())
    if not folders:
        return [f"No incident folders found under {incident_root}"]
    errors = [error for folder in folders for error in validate_incident_folder(folder)]
    if len(folders) != 5:
        errors.append(f"Expected 5 incident folders, found {len(folders)}")
    return errors


if __name__ == "__main__":
    validation_errors = validate_dataset()
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Validated 5 incident folders successfully.")
