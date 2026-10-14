FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini .

RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
USER 10001:10001

EXPOSE 8000
CMD ["python", "-m", "src.server"]
