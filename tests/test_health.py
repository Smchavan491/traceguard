from unittest.mock import MagicMock

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok_when_database_is_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = MagicMock()
    monkeypatch.setattr("app.main.psycopg.connect", MagicMock(return_value=connection))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
    connection.__enter__.return_value.execute.assert_any_call("SELECT 1")


def test_health_returns_503_when_database_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    connect = MagicMock(side_effect=psycopg.OperationalError("database unavailable"))
    monkeypatch.setattr("app.main.psycopg.connect", connect)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "unreachable"}
