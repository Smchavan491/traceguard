import json
from pathlib import Path
from typing import Any

import pytest

from app.incident_loader import load_incident_for_agent
from scripts.generate_incidents import generate_dataset
from scripts.validate_incidents import validate_dataset


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_generating_twice_produces_identical_files(tmp_path: Path) -> None:
    first_incidents = tmp_path / "first" / "incidents"
    first_runbooks = tmp_path / "first" / "runbooks"
    second_incidents = tmp_path / "second" / "incidents"
    second_runbooks = tmp_path / "second" / "runbooks"

    generate_dataset(first_incidents, first_runbooks)
    generate_dataset(second_incidents, second_runbooks)

    assert _snapshot(first_incidents) == _snapshot(second_incidents)
    assert _snapshot(first_runbooks) == _snapshot(second_runbooks)


def test_generated_dataset_validates_and_has_expected_logs(tmp_path: Path) -> None:
    incident_root = tmp_path / "incidents"
    generate_dataset(incident_root, tmp_path / "runbooks")

    assert validate_dataset(incident_root) == []
    for log_file in incident_root.rglob("logs.json"):
        assert 100 <= len(json.loads(log_file.read_text(encoding="utf-8"))) <= 300


def test_agent_loader_never_opens_ground_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    incident_root = tmp_path / "incidents"
    generate_dataset(incident_root, tmp_path / "runbooks")
    incident_dir = incident_root / "INC-001-bad-deploy-latency"
    original_open = Path.open
    opened_paths: list[Path] = []

    def guarded_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        opened_paths.append(path)
        if path.name == "ground_truth.json":
            raise AssertionError("Agent loader must never open ground_truth.json")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    loaded = load_incident_for_agent(incident_dir)

    assert loaded.incident.incident_id == "INC-001"
    assert len(loaded.logs) == 160
    assert len(loaded.deployments) == 1
    assert loaded.dependency_map.incident_id == "INC-001"
    assert all(path.name != "ground_truth.json" for path in opened_paths)
