###############################
# Multi-stage Dockerfile
# Goal: keep final image slim (no build toolchain) while compiling wheels in builder.
###############################

FROM python:3.11.9-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# System build deps only for build stage (psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential gcc libpq-dev ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./

# Create virtual env to copy later
RUN python -m venv /opt/venv \
	&& /opt/venv/bin/pip install --upgrade pip \
	&& /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

###############################
# Runtime image
###############################
FROM python:3.11.9-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/opt/venv \
	PATH=/opt/venv/bin:$PATH \
	PORT=5001

# Only runtime libs (no compilers). libpq5 needed for psycopg2 binary; ffmpeg kept if document/video processing required.
RUN apt-get update && apt-get install -y --no-install-recommends \
	libpq5 ffmpeg \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY . .

EXPOSE 5001

# Healthcheck (simple TCP) – optional; uncomment if desired
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import socket,os; s=socket.socket(); s.connect(('127.0.0.1', int(os.environ.get('PORT',5001)))); s.close()" || exit 1

# Run migrations then start Gunicorn
CMD ["/bin/sh", "-c", "flask --app manage.py db-upgrade && gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 wsgi:app"]