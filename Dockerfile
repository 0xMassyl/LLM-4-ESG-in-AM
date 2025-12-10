# Use a stable base OS (Debian Bookworm) instead of a moving target like slim.
# Helps avoid unexpected breaking changes when rebuilding the image.
FROM python:3.11-slim-bookworm

# Environment variables to define runtime behavior.
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    POETRY_VERSION=1.7.1

WORKDIR /app





# -----------------------------------------------------------
# 1. Install essential SYSTEM dependencies
# -----------------------------------------------------------
# These are needed for Python packages that compile native code.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# -----------------------------------------------------------
# 2. Install Poetry (Python dependency manager)
# -----------------------------------------------------------
RUN pip install "poetry==$POETRY_VERSION"

# -----------------------------------------------------------
# 3. Copy dependency configuration files
# -----------------------------------------------------------
COPY pyproject.toml poetry.lock* /app/

# -----------------------------------------------------------
# 4. Install Python dependencies
# -----------------------------------------------------------
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# -----------------------------------------------------------
# 5. Install Playwright and its required Linux dependencies
# -----------------------------------------------------------
RUN playwright install --with-deps chromium

# -----------------------------------------------------------
# 6. Copy the full source code into the container
# -----------------------------------------------------------
COPY . /app

# -----------------------------------------------------------
# Security: switch to a non-root user
# -----------------------------------------------------------
RUN useradd -m appuser
USER appuser

# -------------------------------
