"""FastAPI web API for the existing SmartExtract Gemini service."""

from __future__ import annotations

import json
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.middleware.sessions import SessionMiddleware

from schemas.invoice_schema import InvoiceSchema
from schemas.resume_schema import ResumeSchema
from services.gemini_service import (
    GeminiServiceError,
    extract_invoice_information,
    extract_resume_information,
)

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

SESSION_SECRET = os.getenv("SMARTEXTRACT_SESSION_SECRET", "")
if len(SESSION_SECRET) < 32 or SESSION_SECRET.startswith("replace-"):
    raise RuntimeError(
        "Set SMARTEXTRACT_SESSION_SECRET in .env to a random value of at least "
        "32 characters before starting the API."
    )

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
PASSWORD_ITERATIONS = 600_000
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _database_path() -> Path:
    configured_path = Path(
        os.getenv("SMARTEXTRACT_DATABASE_PATH", ".data/smartextract.db")
    ).expanduser()
    if not configured_path.is_absolute():
        configured_path = PROJECT_ROOT / configured_path
    return configured_path


@contextmanager
def _database() -> Iterator[sqlite3.Connection]:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _initialize_database() -> None:
    with _database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_iterations INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                document_type TEXT NOT NULL
                    CHECK (document_type IN ('invoice', 'resume')),
                status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
                result_json TEXT,
                error_message TEXT,
                processed_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS extractions_user_date_idx
                ON extractions(user_id, processed_at DESC);
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    _initialize_database()
    yield


app = FastAPI(
    title="SmartExtract API",
    description="Authenticated API for Gemini-backed invoice and resume extraction.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=os.getenv("SMARTEXTRACT_COOKIE_SECURE", "").lower()
    in {"1", "true", "yes"},
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=256)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Full name cannot be blank.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class DocumentTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_text: str = Field(min_length=1, max_length=2_000_000)

    @field_validator("document_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The uploaded text file is empty.")
        return value


def _hash_password(password: str) -> tuple[str, str, int]:
    salt = secrets.token_bytes(16)
    password_hash = pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return salt.hex(), password_hash.hex(), PASSWORD_ITERATIONS


def _password_matches(
    password: str,
    salt_hex: str,
    expected_hash_hex: str,
    iterations: int,
) -> bool:
    actual_hash = pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations
    ).hex()
    return compare_digest(actual_hash, expected_hash_hex)


def _public_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


def _current_user(request: Request) -> dict[str, Any]:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=401, detail="Please sign in to continue.")

    with _database() as connection:
        row = connection.execute(
            "SELECT id, full_name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return _public_user(row)


def _record_extraction(
    user_id: int,
    document_type: Literal["invoice", "resume"],
    status: Literal["success", "failed"],
    result: dict[str, Any] | None,
    error_message: str | None,
) -> dict[str, Any]:
    processed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result_json = (
        json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if result is not None
        else None
    )
    with _database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO extractions
                (user_id, document_type, status, result_json, error_message, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                document_type,
                status,
                result_json,
                error_message,
                processed_at,
            ),
        )
        extraction_id = cursor.lastrowid

    return {
        "id": extraction_id,
        "document_type": document_type,
        "status": status,
        "processed_at": processed_at,
        "data": result,
        "error": error_message,
    }


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, request: Request) -> dict[str, Any]:
    salt, password_hash, iterations = _hash_password(payload.password)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with _database() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users
                    (full_name, email, password_salt, password_hash,
                     password_iterations, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.full_name,
                    payload.email,
                    salt,
                    password_hash,
                    iterations,
                    created_at,
                ),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists."
        ) from None

    request.session.clear()
    request.session["user_id"] = user_id
    return {
        "user": {
            "id": user_id,
            "full_name": payload.full_name,
            "email": payload.email,
            "created_at": created_at,
        }
    }


@app.post("/api/auth/login")
def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    with _database() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, email, password_salt, password_hash,
                   password_iterations, created_at
            FROM users WHERE email = ? COLLATE NOCASE
            """,
            (payload.email,),
        ).fetchone()

    if row is None or not _password_matches(
        payload.password,
        row["password_salt"],
        row["password_hash"],
        row["password_iterations"],
    ):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    request.session.clear()
    request.session["user_id"] = row["id"]
    return {"user": _public_user(row)}


@app.post("/api/auth/logout", status_code=204)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=204)


@app.get("/api/auth/me")
def get_current_user(user: dict[str, Any] = Depends(_current_user)) -> dict[str, Any]:
    return {"user": user}


def _extract(
    document_type: Literal["invoice", "resume"],
    payload: DocumentTextRequest,
    user: dict[str, Any],
) -> dict[str, Any]:
    extractor = (
        extract_invoice_information
        if document_type == "invoice"
        else extract_resume_information
    )

    try:
        extracted = extractor(payload.document_text)
    except ValueError as exc:
        _record_extraction(
            user["id"], document_type, "failed", None, str(exc)
        )
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except GeminiServiceError as exc:
        _record_extraction(
            user["id"], document_type, "failed", None, str(exc)
        )
        raise HTTPException(status_code=502, detail=str(exc)) from None

    if not isinstance(extracted, (InvoiceSchema, ResumeSchema)):
        raise RuntimeError("The extraction service returned an unexpected model.")

    return _record_extraction(
        user["id"],
        document_type,
        "success",
        extracted.model_dump(mode="json"),
        None,
    )


@app.post("/api/extract/invoice")
def extract_invoice(
    payload: DocumentTextRequest,
    user: dict[str, Any] = Depends(_current_user),
) -> dict[str, Any]:
    return _extract("invoice", payload, user)


@app.post("/api/extract/resume")
def extract_resume(
    payload: DocumentTextRequest,
    user: dict[str, Any] = Depends(_current_user),
) -> dict[str, Any]:
    return _extract("resume", payload, user)


@app.get("/api/extractions/history")
def get_extraction_history(
    user: dict[str, Any] = Depends(_current_user),
) -> dict[str, Any]:
    with _database() as connection:
        stats_row = connection.execute(
            """
            SELECT COUNT(*) AS total_documents,
                   COALESCE(SUM(status = 'success'), 0) AS successful_extractions,
                   COALESCE(SUM(status = 'failed'), 0) AS failed_extractions
            FROM extractions WHERE user_id = ?
            """,
            (user["id"],),
        ).fetchone()
        rows = connection.execute(
            """
            SELECT id, document_type, status, result_json, error_message, processed_at
            FROM extractions
            WHERE user_id = ?
            ORDER BY processed_at DESC, id DESC
            LIMIT 100
            """,
            (user["id"],),
        ).fetchall()

    records = [
        {
            "id": row["id"],
            "document_type": row["document_type"],
            "status": row["status"],
            "processed_at": row["processed_at"],
            "data": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": row["error_message"],
        }
        for row in rows
    ]
    return {"stats": dict(stats_row), "records": records}


app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend",
)
