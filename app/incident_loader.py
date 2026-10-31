import json
from pathlib import Path

from app.schemas import AgentIncidentData, DependencyMap, DeploymentEvent, Incident, LogLine


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_incident_for_agent(incident_dir: Path) -> AgentIncidentData:
    """Load only agent-visible incident evidence; ground truth is never opened."""
    return AgentIncidentData(
        incident=Incident.model_validate(_read_json(incident_dir / "incident.json")),
        logs=[LogLine.model_validate(item) for item in _read_json(incident_dir / "logs.json")],
        deployments=[
            DeploymentEvent.model_validate(item)
            for item in _read_json(incident_dir / "deployments.json")
        ],
        dependency_map=DependencyMap.model_validate(
            _read_json(incident_dir / "dependency_map.json")
        ),
    )
