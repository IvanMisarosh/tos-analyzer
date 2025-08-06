# Terms & Conditions Analyzer

## Description

This project is an LLM-powered analyzer for Terms & Conditions (ToS) documents. It enables users to upload PDF files, automatically analyzes their clauses and chapters using Google Gemini, and provides risk assessments and key insights for consumer protection. The system supports user authentication, document management, and scalable background processing via Celery.

## Features

- **User Authentication:** Secure registration and login using JWT.
- **Document Upload:** Accepts PDF files and stores them for analysis.
- **Automated Analysis:** Uses LLM (Google Gemini) to analyze clauses and chapters.
- **Risk Assessment:** Categorizes clauses and rates consumer risk.
- **Background Processing:** Asynchronous analysis via Celery tasks.
- **Rate & Concurrency Limiting:** Prevents abuse of LLM API.
- **MongoDB Storage:** Stores clause analysis results for fast retrieval.

## Project Structure

```
tos-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entrypoint
│   ├── config.py              # App settings (env vars)
│   ├── models.py              # SQLAlchemy models (User, Document)
│   ├── enums.py               # Enum types (statuses, risk levels)
│   ├── constants.py           # Clause categories
│   ├── logger.py              # Logging setup
│   ├── celery.py              # Celery configuration
│   ├── tasks.py               # Celery tasks (document analysis)
│   ├── utils.py               # Utility functions (file saving, analyzer service)
│   ├── analyzer/              # Document analysis logic
│   │   ├── routes.py          # API endpoints for analysis
│   │   ├── schemas.py         # Pydantic models for analysis
│   │   ├── llm_analyzer.py    # LLM-based clause analysis
│   │   ├── pdf_parser.py      # PDF parsing and chapter extraction
│   │   ├── service.py         # Analyzer service orchestration
│   │   ├── templates.py       # Prompt templates for LLM
│   │   ├── rate_limiter.py    # API rate limiting
│   │   ├── concurrency_limiter.py # Concurrency limiting
│   │   ├── document_repository.py # DB access for documents
│   ├── auth/                  # Authentication logic
│   │   ├── routes.py          # Auth endpoints
│   │   ├── schemas.py         # Pydantic models for auth
│   │   ├── dependencies.py    # Auth dependencies for FastAPI
│   │   ├── service.py         # Auth service (JWT, password hashing)
│   ├── db/
│   │   ├── db.py              # SQLAlchemy DB setup
│   │   ├── mongo.py           # MongoDB setup
├── alembic/                   # Database migrations
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   ├── versions/
│   │   ├── <migration files>.py
├── uploads/                   # Uploaded PDF files (created at runtime)
├── .env                       # Environment variables (not committed)
```

## Setup & Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd tos-analyzer
   ```

2. **Create and activate a Python virtual environment:**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in required values (DB URLs, API keys, secrets).

5. **Run database migrations:**
   ```sh
   alembic upgrade head
   ```

## Running the Application

### 1. Start the FastAPI server

```sh
uvicorn app.main:app --reload
```

- The API will be available at `http://localhost:8000`

### 2. Start the Celery worker

```sh
celery -A app.celery.celery worker --loglevel=info
```
#### 2.1 For windows
```sh
celery -A app  worker --pool=threads --loglevel=info
```
- Celery will process document analysis tasks in the background.

### 3. MongoDB & Redis

- Ensure MongoDB and Redis are running and accessible at the URIs specified in `.env`.

## API Endpoints

### Authentication

- `POST /auth/register` — Register a new user.
- `POST /auth/token` — Obtain JWT token.

### Document Management

- `POST /document/` — Upload a PDF document.
- `GET /documents/` — List user's documents.
- `GET /document/{id}` — Get document details.
- `GET /document/{id}/status` — Check analysis status.
- `POST /document/{id}/analyze` — Start analysis (background task).
- `GET /document/{id}/clauses` — Get clause analysis results.

## Configuration Parameters

All configuration is managed via environment variables in `.env`:

- `DATABASE_URL` — SQLAlchemy DB URI
- `GOOGLE_API_KEY` — API key for Gemini LLM
- `MONGO_URI` — MongoDB URI
- `CELERY_BROKER_URL` — Celery broker (e.g., Redis)
- `SECRET_KEY` — JWT secret
- `LLM_MODEL_NAME`, `LLM_TEMPERATURE`, etc. — LLM settings

See [`app/config.py`](app/config.py) for all available settings.

## Notes

- Uploaded files are saved in the `uploads/` folder.
- Clause analysis results are stored in MongoDB for fast retrieval.
- Rate and concurrency limits are enforced for LLM API usage.
- All migrations are managed via Alembic (`alembic/` folder).

---