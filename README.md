# SmartExtract

SmartExtract converts unstructured invoice and resume text into Pydantic-
validated JSON with Google Gemini. It includes a responsive web workspace,
authenticated FastAPI endpoints, a local SQLite history, and the original CLI.

## Requirements and setup

Use Python 3.11 or newer. From the project directory:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- Replace `GEMINI_API_KEY` with your own Gemini API key.
- Leave `GEMINI_MODEL=gemini-2.5-flash` or choose another supported model.
- Replace `SMARTEXTRACT_SESSION_SECRET` with a random value of at least 32
  characters. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `SMARTEXTRACT_DATABASE_PATH` defaults to `.data/smartextract.db`.

Never commit `.env` or share your API key or session secret. `.env`, the local
database directory, and generated `output.json` are excluded by `.gitignore`.
Submitted document text is sent to Google Gemini; only process documents you
are authorized to share with that service.

## Run the web application

Start the FastAPI server from the project directory with the virtual environment
active:

```sh
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). FastAPI serves the frontend
and `/api` endpoints from the same origin, so no separate frontend server or
CORS configuration is needed. Register an account, then use the invoice or
resume workflow to upload a UTF-8 `.txt` document (maximum 2 MB). The frontend
shows the backend's validated response and can download that JSON.

The app uses an HttpOnly, SameSite signed session cookie. For HTTPS deployments,
set `SMARTEXTRACT_COOKIE_SECURE=true`; do not use that option for plain HTTP
localhost. The API key remains on the backend. Passwords are stored as salted
PBKDF2-HMAC-SHA256 hashes; document text is not stored in extraction history.

## API

- `POST /api/auth/register` — create an account and start a session.
- `POST /api/auth/login` — authenticate and start a session.
- `POST /api/auth/logout` — clear the current session.
- `GET /api/auth/me` — return the authenticated account.
- `POST /api/extract/invoice` — extract invoice fields (authentication required).
- `POST /api/extract/resume` — extract resume fields (authentication required).
- `GET /api/extractions/history` — return the account's recent records and
  aggregate counts (authentication required).

Extraction requests accept `{"document_text": "..."}`. Successful responses
include `id`, `document_type`, `status`, `processed_at`, and validated `data`.
The history contains up to 100 latest records; aggregate counts cover all
records for the account.

## Run the CLI

The original command-line interface remains available:

```sh
python main.py
```

Choose **Invoice Extraction** or **Resume Extraction** and enter a `.txt` path.
The validated JSON is displayed and written to `output.json`.

## Architecture

- `frontend/` — responsive HTML/CSS/JavaScript client; renders only backend
  extraction results and uses same-origin authenticated requests.
- `api.py` — FastAPI routes, session authentication, password hashing, SQLite
  account/history persistence, and static frontend hosting.
- `services/gemini_service.py` — existing Gemini client and extraction calls.
- `prompts/templates.py` — existing parameterized, source-grounded prompts.
- `schemas/` — existing Pydantic invoice/resume schemas reused by the API.
- `main.py` — original interactive CLI.
- `samples/` — fictional invoice and resume demo inputs.
- `tests/test_extractor.py` and `tests/test_api.py` — mocked Gemini, schema,
  authentication, history, and CLI tests; no live Gemini calls are made.
- `extract_document.py` — optional, separate OpenAI text-to-JSON utility.

## Tests

With the virtual environment active:

```sh
pytest -v
```

The tests mock Gemini and do not require a key or make paid Gemini calls.

## Limitations

The website accepts plain-text `.txt` files only; it does not perform PDF or
image OCR. Profile editing, password reset, and account deletion are not
implemented. This local SQLite/session setup is suitable for a development
demo, not a production deployment without additional operational controls such
as HTTPS, rate limiting, backup/retention policies, and account recovery.