# Birthday AI Agent Backend

Backend for a birthday planning AI agent using FastAPI, SQLAlchemy, JWT auth, SQLite, and GigaChat.

## Quick start

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

## Notes

- The project uses SQLite by default (`app.db`).
- CORS is open for local frontend development.
- GigaChat credentials are loaded from `.env`.
- If you share this project with someone else, rotate the credentials first.


## Places recommendations

Add `DGIS_API_KEY` to `.env` to enable real venue search via 2GIS Places API.
Optional: `DGIS_BASE_URL`, `DGIS_TIMEOUT_SECONDS`.
