FROM python:3.14.4-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1 
ENV UV_PROJECT_ENVIRONMENT="/opt/venv" 
ENV PATH="/opt/venv/bin:$PATH"

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
# исп python из базового образа 
ENV UV_PYTHON_DOWNLOADS=0 

WORKDIR /app

# build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project

COPY . /app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]