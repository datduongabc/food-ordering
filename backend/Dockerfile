FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

# Dependencies first, so code changes reuse the cached layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
# Seeded dish photos. Compose mounts a volume at /app/media so uploads survive rebuilds; a
# volume is filled from the image only when first created, so each start copies across any
# seeded photo it lacks (from a newer menu migration), never overwriting what is there.
COPY media ./seed-media

RUN useradd --system --create-home app && mkdir media && chown -R app:app /app/media
USER app

EXPOSE 8000
# Seeded photos are synced and migrations run on every start; both are no-ops once current.
# The app logs each request itself, with its id, so uvicorn's access log would only repeat it.
CMD ["sh", "-c", "cp -rT --update=none seed-media media && alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' --no-access-log"]
