FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY tests ./tests
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --frozen --all-groups

CMD ["uv", "run", "pytest", "tests/", "-q"]
