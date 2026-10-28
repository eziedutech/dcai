# dcAI backend. Build from the repository root:
#   docker build -f code/backpy/Dockerfile .
# The layout inside the image mirrors the repo (/srv/code/backpy, /srv/data), because the
# app finds data/ relative to its own path.
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/srv/venv PATH="/srv/venv/bin:$PATH"

WORKDIR /srv/code/backpy
COPY code/backpy/pyproject.toml code/backpy/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY code/backpy/alembic.ini ./
COPY code/backpy/migrations ./migrations
COPY code/backpy/app ./app
COPY code/backpy/deploy/start.sh ./start.sh
COPY data/guide /srv/data/guide

RUN useradd --system --uid 10001 dcai && mkdir -p /srv/lists && chown dcai /srv/lists && chmod +x start.sh
USER dcai
ENV SITE_LISTS_DIR=/srv/lists DCAI_SKIP_DOTENV=1
EXPOSE 8000
CMD ["./start.sh"]
