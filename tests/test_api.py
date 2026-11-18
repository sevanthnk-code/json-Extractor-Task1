import os
from collections.abc import Iterator
from pathlib import Path

os.environ.setdefault(
    "SMARTEXTRACT_SESSION_SECRET",
    "test-session-secret-with-more-than-32-characters",
)

import pytest
from fastapi.testclient import TestClient

import api
from schemas.invoice_schema import InvoiceSchema
from schemas.resume_schema import ResumeSchema
from services.gemini_service import GeminiServiceError


@pytest.fixture
def client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv(
        "SMARTEXTRACT_DATABASE_PATH",
        str(tmp_path / "smartextract-test.db"),
    )
    with TestClient(api.app) as test_client:
        yield test_client


def register(client: TestClient, email: str = "riley@example.com") -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Riley Hart",
            "email": email,
            "password": "a-strong-password-123",
        },
    )
    assert response.status_code == 201


def test_history_requires_an_authenticated_session(client: TestClient) -> None:
    response = client.get("/api/extractions/history")

    assert response.status_code == 401


def test_register_login_and_logout_manage_authenticated_session(
    client: TestClient,
) -> None:
    register(client)
    assert client.get("/api/auth/me").json()["user"]["email"] == "riley@example.com"

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401

    response = client.post(
        "/api/auth/login",
        json={"email": "RILEY@example.com", "password": "a-strong-password-123"},
    )
    assert response.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_duplicate_registration_and_wrong_password_are_rejected(
    client: TestClient,
) -> None:
    register(client)

    duplicate = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another Person",
            "email": "RILEY@example.com",
            "password": "a-different-password-456",
        },
    )
    wrong_password = client.post(
        "/api/auth/login",
        json={"email": "riley@example.com", "password": "incorrect-password"},
    )

    assert duplicate.status_code == 409
    assert wrong_password.status_code == 401


def test_invoice_response_and_history_use_validated_service_data(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register(client)
    monkeypatch.setattr(
        api,
        "extract_invoice_information",
        lambda _: InvoiceSchema(invoice_number="INV-TEST", total_amount=125.0),
    )

    response = client.post(
        "/api/extract/invoice",
        json={"document_text": "Invoice number INV-TEST. Total INR 125."},
    )
    history = client.get("/api/extractions/history").json()

    assert response.status_code == 200
    assert response.json()["data"]["invoice_number"] == "INV-TEST"
    assert response.json()["data"]["total_amount"] == 125.0
    assert history["stats"]["successful_extractions"] == 1
    assert history["records"][0]["data"] == response.json()["data"]


def test_resume_endpoint_uses_the_existing_resume_schema(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register(client)
    monkeypatch.setattr(
        api,
        "extract_resume_information",
        lambda _: ResumeSchema(full_name="Morgan Lee", skills=["Python"]),
    )

    response = client.post(
        "/api/extract/resume",
        json={"document_text": "Morgan Lee. Python."},
    )

    assert response.status_code == 200
    assert response.json()["data"]["full_name"] == "Morgan Lee"
    assert response.json()["data"]["skills"] == ["Python"]


def test_gemini_failures_are_reported_and_recorded(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register(client)

    def fail_extraction(_: str) -> InvoiceSchema:
        raise GeminiServiceError("Gemini API request failed.")

    monkeypatch.setattr(api, "extract_invoice_information", fail_extraction)
    response = client.post(
        "/api/extract/invoice",
        json={"document_text": "Invoice text"},
    )
    history = client.get("/api/extractions/history").json()

    assert response.status_code == 502
    assert history["stats"]["failed_extractions"] == 1
    assert history["records"][0]["status"] == "failed"
    assert history["records"][0]["data"] is None