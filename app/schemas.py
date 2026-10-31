from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(pattern=r"^INC-\d{3}$")
    symptom: str = Field(min_length=1)
    service: str = Field(min_length=1)
    started_at: datetime


class LogLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_id: str = Field(min_length=1)
    timestamp: datetime
    service: str = Field(min_length=1)
    level: Literal["INFO", "WARN", "ERROR"]
    message: str = Field(min_length=1)


class DeploymentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deployment_id: str = Field(min_length=1)
    timestamp: datetime
    service: str = Field(min_length=1)
    version: str = Field(min_length=1)
    previous_version: str | None = None
    summary: str = Field(min_length=1)


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dependency_id: str = Field(min_length=1)
    caller: str = Field(min_length=1)
    callee: str = Field(min_length=1)


class DependencyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dependency_map_id: str = Field(min_length=1)
    incident_id: str = Field(pattern=r"^INC-\d{3}$")
    edges: list[DependencyEdge]


class GroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ground_truth_id: str = Field(min_length=1)
    incident_id: str = Field(pattern=r"^INC-\d{3}$")
    root_cause: str = Field(min_length=1)
    key_evidence_ids: list[str]
    correct_action: str = Field(min_length=1)
    difficulty: Literal["clear", "ambiguous", "missing", "adversarial"]
    expected_behavior: Literal["diagnose", "abstain", "ask_for_info", "ignore_injection"]
    acceptable_causes: list[str] | None = None


class AgentIncidentData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident: Incident
    logs: list[LogLine]
    deployments: list[DeploymentEvent]
    dependency_map: DependencyMap
