#!/usr/bin/env python3
"""Interactive SmartExtract command-line application."""

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ValidationError

from services.gemini_service import (
    GeminiServiceError,
    extract_invoice_information,
    extract_resume_information,
)

WELCOME_SCREEN = "SMARTEXTRACT – AI STRUCTURED DATA EXTRACTOR"
OUTPUT_PATH = Path("output.json")

DocumentExtractor = Callable[[str], BaseModel]
DOCUMENT_TYPES: dict[str, tuple[str, DocumentExtractor]] = {
    "1": ("Invoice", extract_invoice_information),
    "2": ("Resume", extract_resume_information),
}


def select_document_type() -> tuple[str, DocumentExtractor]:
    """Prompt until the user selects one of the supported document types."""
    print("\n1. Invoice Extraction")
    print("2. Resume Extraction")

    while True:
        choice = input("Select document type (1 or 2): ").strip()
        try:
            return DOCUMENT_TYPES[choice]
        except KeyError:
            print("Invalid document type. Please enter 1 or 2.")


def read_document_text(path_text: str) -> str:
    """Read a non-empty UTF-8 .txt file from the supplied path."""
    cleaned_path = path_text.strip()
    if (
        len(cleaned_path) >= 2
        and cleaned_path[0] == cleaned_path[-1]
        and cleaned_path[0] in {"'", '"'}
    ):
        cleaned_path = cleaned_path[1:-1]

    if not cleaned_path:
        raise ValueError("Please enter a path to a .txt file.")

    document_path = Path(cleaned_path).expanduser()
    if document_path.suffix.lower() != ".txt":
        raise ValueError("The document must be a .txt file.")

    try:
        document_text = document_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {document_path}") from None
    except IsADirectoryError:
        raise ValueError(
            f"Expected a .txt file, but this path is a directory: {document_path}"
        ) from None

    if not document_text.strip():
        raise ValueError("The selected text file is empty.")
    return document_text


def save_output_json(json_text: str) -> None:
    """Write the formatted extraction JSON to the current directory."""
    try:
        OUTPUT_PATH.write_text(json_text + "\n", encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            f"Permission denied while saving the extraction to {OUTPUT_PATH}."
        ) from exc
    except OSError as exc:
        raise OSError(f"Could not save the extraction to {OUTPUT_PATH}: {exc}") from exc


def main() -> int:
    print(WELCOME_SCREEN)
    print("=" * len(WELCOME_SCREEN))

    try:
        document_type, extractor = select_document_type()
        path_text = input("Enter the path to your .txt file: ")
        document_text = read_document_text(path_text)

        print(f"\nExtracting {document_type.lower()} information...")
        result = extractor(document_text)
        json_output = result.model_dump_json(indent=2)
        save_output_json(json_output)

        print("\nExtraction complete:\n")
        print(json_output)
        print(f"\nSaved the result to {OUTPUT_PATH.resolve()}")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
    except PermissionError:
        print(
            "Error: permission denied while reading the document or saving output.json."
        )
    except UnicodeDecodeError:
        print("Error: the file is not valid UTF-8 text.")
    except GeminiServiceError as exc:
        print(f"Extraction error: {exc}")
    except ValidationError:
        print("Error: extracted data did not pass schema validation.")
    except ValueError as exc:
        print(f"Input error: {exc}")
    except OSError as exc:
        print(f"File error: {exc}")
    except (EOFError, KeyboardInterrupt):
        print("\nExtraction cancelled.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
