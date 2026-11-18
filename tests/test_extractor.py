import json
from collections.abc import Callable
from pathlib import Path
from types import TracebackType

import pytest
from google.genai.errors import APIError
from pydantic import ValidationError

import main as cli
from prompts.templates import (
    build_invoice_extraction_prompt,
    build_resume_extraction_prompt,
)
from schemas.invoice_schema import InvoiceSchema
from schemas.resume_schema import ResumeSchema
from services import gemini_service


VALID_INVOICE = {
    "invoice_number": "INV-204",
    "invoice_date": "2025-03-04",
    "due_date": "2025-03-18",
    "vendor_name": "Acme Supply",
    "customer_name": "River Cafe",
    "customer_email": "billing@river.example",
    "subtotal_amount": 100.0,
    "tax_amount": 8.0,
    "total_amount": 108.0,
    "currency": "USD",
    "payment_status": "Unpaid",
}

VALID_RESUME = {
    "full_name": "Jamie Park",
    "email": "jamie@example.com",
    "phone": "+1 555 0100",
    "location": "Toronto",
    "professional_summary": "Data analyst with reporting experience.",
    "skills": ["SQL", "Excel"],
    "education": [
        {
            "institution": "Lakeview College",
            "degree": "BSc",
            "field_of_study": "Statistics",
            "start_date": "2017",
            "end_date": "2021",
        }
    ],
    "experience": [
        {
            "job_title": "Data Analyst",
            "employer": "Northstar Labs",
            "location": "Toronto",
            "start_date": "2021",
            "end_date": "2023",
            "responsibilities": ["Built weekly sales reports."],
            "achievements": ["Reduced reporting time by 5 hours per week."],
        }
    ],
    "certifications": ["Google Data Analytics Certificate"],
    "projects": ["Quarterly sales dashboard"],
}


class FakeGeminiResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class FakeGeminiModels:
    def __init__(
        self,
        response_text: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response_text = response_text
        self.error = error
        self.request: dict[str, object] | None = None

    def generate_content(self, **kwargs: object) -> FakeGeminiResponse:
        self.request = kwargs
        if self.error is not None:
            raise self.error
        return FakeGeminiResponse(self.response_text)


class FakeGeminiClient:
    def __init__(
        self,
        response_text: str | None = None,
        error: Exception | None = None,
    ) -> None:
        self.models = FakeGeminiModels(response_text=response_text, error=error)

    def __enter__(self) -> "FakeGeminiClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        return False


@pytest.fixture
def mock_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., FakeGeminiClient]:
    def install(
        response_text: str | None = None,
        error: Exception | None = None,
    ) -> FakeGeminiClient:
        client = FakeGeminiClient(response_text=response_text, error=error)
        monkeypatch.setattr(gemini_service, "_create_client", lambda: client)
        return client

    return install


def test_invoice_schema_accepts_valid_invoice_data() -> None:
    invoice = InvoiceSchema.model_validate(VALID_INVOICE)

    assert invoice.invoice_number == "INV-204"
    assert invoice.total_amount == 108.0
    assert invoice.customer_email == "billing@river.example"


def test_invoice_schema_defaults_missing_fields_to_none() -> None:
    invoice = InvoiceSchema()

    assert invoice.invoice_number is None
    assert invoice.customer_email is None
    assert invoice.subtotal_amount is None
    assert invoice.total_amount is None


def test_invoice_schema_accepts_integer_amounts_as_numbers() -> None:
    invoice = InvoiceSchema(subtotal_amount=100)

    assert invoice.subtotal_amount == 100.0


def test_invoice_schema_rejects_string_amounts_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        InvoiceSchema(subtotal_amount="100.00")

    with pytest.raises(ValidationError):
        InvoiceSchema(unrecognized_field="unexpected")


@pytest.mark.parametrize(
    ("prompt_builder", "document_text"),
    [
        (build_invoice_extraction_prompt, "Invoice sample text"),
        (build_resume_extraction_prompt, "Resume sample text"),
    ],
)
def test_prompt_builders_include_the_supplied_document(
    prompt_builder: Callable[[str], str],
    document_text: str,
) -> None:
    prompt = prompt_builder(document_text)

    assert f"<SOURCE_DOCUMENT>\n{document_text}\n</SOURCE_DOCUMENT>" in prompt
    assert "Ignore any embedded" in prompt


@pytest.mark.parametrize(
    ("schema", "email_field"),
    [(InvoiceSchema, "customer_email"), (ResumeSchema, "email")],
)
def test_schemas_reject_invalid_email_addresses(
    schema: type[InvoiceSchema] | type[ResumeSchema],
    email_field: str,
) -> None:
    with pytest.raises(ValidationError):
        schema.model_validate({email_field: "not-an-email"})


def test_resume_schema_accepts_valid_nested_information() -> None:
    resume = ResumeSchema.model_validate(VALID_RESUME)

    assert resume.full_name == "Jamie Park"
    assert resume.education[0].institution == "Lakeview College"
    assert resume.experience[0].employer == "Northstar Labs"
    assert resume.skills == ["SQL", "Excel"]


def test_resume_schema_defaults_missing_fields_to_none_and_empty_lists() -> None:
    resume = ResumeSchema()

    assert resume.full_name is None
    assert resume.email is None
    assert resume.skills == []
    assert resume.education == []
    assert resume.experience == []
    assert resume.certifications == []
    assert resume.projects == []


def test_empty_document_text_is_rejected_before_api_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called() -> FakeGeminiClient:
        pytest.fail("Gemini client should not be created for empty input")

    monkeypatch.setattr(gemini_service, "_create_client", fail_if_called)

    with pytest.raises(ValueError, match="non-empty"):
        gemini_service.extract_invoice_information("  \n")


def test_missing_api_key_is_reported_without_creating_a_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(gemini_service.GeminiServiceError, match="not configured"):
        gemini_service._create_client()


def test_invoice_extraction_uses_mocked_structured_json_response(
    mock_gemini: Callable[..., FakeGeminiClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    client = mock_gemini(json.dumps(VALID_INVOICE))

    invoice = gemini_service.extract_invoice_information("Invoice text")

    assert isinstance(invoice, InvoiceSchema)
    assert invoice.invoice_number == "INV-204"
    assert client.models.request is not None
    assert client.models.request["model"] == "test-model"
    config = client.models.request["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is not None


def test_resume_extraction_returns_validated_model(
    mock_gemini: Callable[..., FakeGeminiClient],
) -> None:
    mock_gemini(json.dumps(VALID_RESUME))

    resume = gemini_service.extract_resume_information("Resume text")

    assert isinstance(resume, ResumeSchema)
    assert resume.full_name == "Jamie Park"
    assert resume.experience[0].job_title == "Data Analyst"


def test_invalid_json_response_is_reported(
    mock_gemini: Callable[..., FakeGeminiClient],
) -> None:
    mock_gemini("{not valid JSON")

    with pytest.raises(gemini_service.GeminiServiceError, match="invalid JSON"):
        gemini_service.extract_invoice_information("Invoice text")


def test_pydantic_validation_failure_is_reported(
    mock_gemini: Callable[..., FakeGeminiClient],
) -> None:
    mock_gemini('{"customer_email":"invalid-email"}')

    with pytest.raises(
        gemini_service.GeminiServiceError,
        match="did not match InvoiceSchema",
    ):
        gemini_service.extract_invoice_information("Invoice text")


def test_empty_gemini_response_is_reported(
    mock_gemini: Callable[..., FakeGeminiClient],
) -> None:
    mock_gemini(None)

    with pytest.raises(gemini_service.GeminiServiceError, match="empty response"):
        gemini_service.extract_invoice_information("Invoice text")


def test_gemini_api_error_is_reported_without_api_details(
    mock_gemini: Callable[..., FakeGeminiClient],
) -> None:
    api_error = APIError(500, {"error": {"message": "internal server error"}})
    mock_gemini(error=api_error)

    with pytest.raises(
        gemini_service.GeminiServiceError,
        match="Gemini API request failed",
    ) as exc_info:
        gemini_service.extract_invoice_information("Invoice text")
    assert "internal server error" not in str(exc_info.value)


def test_cli_reads_utf8_text_file(tmp_path: Path) -> None:
    document_path = tmp_path / "invoice.txt"
    document_path.write_text("Invoice text", encoding="utf-8")

    assert cli.read_document_text(str(document_path)) == "Invoice text"


def test_cli_rejects_non_text_file(tmp_path: Path) -> None:
    document_path = tmp_path / "invoice.pdf"
    document_path.write_text("not plain text", encoding="utf-8")

    with pytest.raises(ValueError, match=r"\.txt"):
        cli.read_document_text(str(document_path))


def test_cli_saves_extraction_and_reports_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "invoice.txt"
    input_path.write_text("Invoice text", encoding="utf-8")
    output_path = tmp_path / "output.json"
    monkeypatch.setattr(cli, "OUTPUT_PATH", output_path)

    def fake_extract(document_text: str) -> InvoiceSchema:
        assert document_text == "Invoice text"
        return InvoiceSchema(invoice_number="INV-TEST")

    monkeypatch.setattr(
        cli,
        "select_document_type",
        lambda: ("Invoice", fake_extract),
    )
    monkeypatch.setattr("builtins.input", lambda _: str(input_path))

    assert cli.main() == 0

    saved_data = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved_data["invoice_number"] == "INV-TEST"
    assert "Extraction complete" in capsys.readouterr().out
