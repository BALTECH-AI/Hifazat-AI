from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError


def test_database_health_does_not_expose_database_details(
    anonymous_client,
    monkeypatch,
):
    connection = MagicMock()
    connection.__enter__.return_value = connection

    mock_engine = MagicMock()
    mock_engine.connect.return_value = connection

    monkeypatch.setattr("app.main.engine", mock_engine)

    response = anonymous_client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_hides_internal_error_details(
    anonymous_client,
    monkeypatch,
):
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SQLAlchemyError(
        "Sensitive database connection details"
    )

    monkeypatch.setattr("app.main.engine", mock_engine)

    response = anonymous_client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database connection failed"
    }
    assert "Sensitive" not in response.text
