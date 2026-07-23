# Competitor Intelligence AI Agent

Continuous competitive intelligence collection, analysis, and diff-detection dashboard built with modern Python (3.12+), FastAPI, Celery, PostgreSQL, PydanticAI, and Model Context Protocol (MCP).

---

## Architecture & Stack

- **API Interface**: FastAPI with asynchronous SQL endpoints & JWT authentication.
- **Asynchronous Pipeline**: Redis + Celery triggers multi-agent tracking queues.
- **AI Orchestrator**: PydanticAI managing sequential Claude 3.5 runs.
- **Research Agents**: Separate dedicated intelligence gathering modules for pricing, news, hiring, and core product changes.
- **Model Context Protocol (MCP)**: Interfaces with Firecrawl (web scraping) and Tavily (web search).
- **Communication Channels**: Automatic PDF compilation via WeasyPrint and delivery via Resend API.

---

## Getting Started

### 1. Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js (for running local MCP servers, optional if using cloud API)

### 2. Installation

Clone the repository and install dependencies using Poetry:

```bash
# Install dependencies
poetry install

# Alternatively, using uv:
uv sync
```

### 3. Local Environment Variables

Copy `.env.example` to `.env` and fill in the required API credentials:

```bash
cp .env.example .env
```

### 4. Running the Database Migrations

Apply SQLAlchemy/Alembic migrations:

```bash
poetry run alembic upgrade head
```

### 5. Running the Application

Start the FastAPI web server locally:

```bash
poetry run uvicorn src.main:app --reload
```

Start the background Celery workers:

```bash
poetry run celery -A src.jobs.celery_app worker --loglevel=info
```

Start Celery Beat scheduler for periodic competitor polling:

```bash
poetry run celery -A src.jobs.celery_app beat --loglevel=info
```

### 6. Running Tests

Run the test suite:

```bash
poetry run pytest tests/
```
