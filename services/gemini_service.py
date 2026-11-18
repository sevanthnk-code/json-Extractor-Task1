import os
from collections.abc import Callable
from typing import TypeVar

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from httpx2 import HTTPError as HttpxError
from pydantic import BaseModel, ValidationError

from prompts.templates import (
    build_invoice_extraction_prompt,
    build_resume_extraction_prompt,
)
from schemas.invoice_schema import InvoiceSchema
from schemas.resume_schema import ResumeSchema

load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class GeminiServiceError(RuntimeError):
    """Raised when Gemini cannot return a valid extraction."""


def _create_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise GeminiServiceError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def _extract_with_schema(
    document_text: str,
    prompt_builder: Callable[[str], str],
    response_schema: type[SchemaT],
) -> SchemaT:
    if not isinstance(document_text, str) or not document_text.strip():
        raise ValueError("document_text must be a non-empty string.")

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
    if not model_name:
        model_name = DEFAULT_GEMINI_MODEL

    prompt = prompt_builder(document_text)
    try:
        with _create_client() as client:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
    except (APIError, HttpxError):
        raise GeminiServiceError(
            "Gemini API request failed. Check API configuration and network connectivity."
        ) from None

    try:
        response_text = response.text
    except ValueError:
        response_text = None

    if not response_text or not response_text.strip():
        raise GeminiServiceError("Gemini returned an empty response.")

    # Keep validation errors generic because they may include source text.
    try:
        return response_schema.model_validate_json(response_text)
    except ValidationError as exc:
        if any(error["type"] == "json_invalid" for error in exc.errors()):
            raise GeminiServiceError("Gemini returned invalid JSON.") from None
        raise GeminiServiceError(
            f"Gemini response did not match {response_schema.__name__}."
        ) from None


def extract_invoice_information(document_text: str) -> InvoiceSchema:
    """Extract and validate invoice information from document text."""
    return _extract_with_schema(
        document_text,
        build_invoice_extraction_prompt,
        InvoiceSchema,
    )


def extract_resume_information(document_text: str) -> ResumeSchema:
    """Extract and validate resume information from document text."""
    return _extract_with_schema(
        document_text,
        build_resume_extraction_prompt,
        ResumeSchema,
    )
