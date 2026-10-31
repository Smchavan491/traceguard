import pytest
from pydantic import ValidationError

from app.schemas import GroundTruth


def test_ground_truth_accepts_expected_behavior_values() -> None:
    for behavior in ("diagnose", "abstain", "ask_for_info", "ignore_injection"):
        model = GroundTruth(
            ground_truth_id="GT-INC001-001",
            incident_id="INC-001",
            root_cause="Synthetic cause",
            key_evidence_ids=["LOG-INC001-001"],
            correct_action="Synthetic action",
            difficulty="clear",
            expected_behavior=behavior,
        )
        assert model.expected_behavior == behavior


def test_ground_truth_rejects_unknown_expected_behavior() -> None:
    with pytest.raises(ValidationError):
        GroundTruth(
            ground_truth_id="GT-INC001-001",
            incident_id="INC-001",
            root_cause="Synthetic cause",
            key_evidence_ids=[],
            correct_action="Synthetic action",
            difficulty="clear",
            expected_behavior="guess",
        )
