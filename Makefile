# Simple Makefile for common tasks (Windows users: use `make` via Git Bash or `mingw32-make`)
# Variables
PY?=python
PIP?=pip
APP?=manage.py
PORT?=5001

.PHONY: help install install-dev run dev upgrade revision lint type test clean docker-build docker-run docker-shell docker-push

help:
	@echo "Available targets:";
	@echo "  install      Install runtime dependencies";
	@echo "  install-dev  Install runtime + dev/test deps";
	@echo "  run          Run app via Flask dev server";
	@echo "  dev          Run gunicorn (production style)";
	@echo "  upgrade      Apply Alembic migrations";
	@echo "  revision     Create new Alembic autogenerate revision (msg=...)";
	@echo "  lint         Run mypy (and ruff if enabled)";
	@echo "  type         Run mypy type checking";
	@echo "  test         Run pytest";
	@echo "  clean        Remove Python cache artifacts";
	@echo "  docker-build Build docker image (IMG, TAG)";
	@echo "  docker-run   Run container mapping port";
	@echo "  docker-shell Open shell inside running container";
	@echo "  docker-push  Push image to registry";

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt

run:
	set FLASK_APP=$(APP) && $(PY) -m flask run -p $(PORT)

# Gunicorn (might need `python -m pip install gunicorn` on Windows WSL / container)
dev:
	gunicorn -w 2 -b 0.0.0.0:$(PORT) wsgi:app

upgrade:
	set FLASK_APP=$(APP) && $(PY) -m flask db upgrade

revision:
	@if [ -z "$(msg)" ]; then echo "Provide msg=YourMessage"; exit 1; fi
	set FLASK_APP=$(APP) && $(PY) -m flask db revision --autogenerate -m "$(msg)"

lint:
	@if command -v ruff >/dev/null 2>&1; then ruff check . ; else echo "ruff not installed"; fi

type:
	mypy . || true

test:
	pytest -q

clean:
	@echo "Removing caches";
	@find . -type d -name __pycache__ -prune -exec rm -rf {} + 2> NUL || true;
	@find . -type f -name '*.pyc' -delete 2> NUL || true;
	@find . -type f -name '.mypy_cache' -delete 2> NUL || true;

# --- Docker ---
IMG?=adv-ia-f
TAG?=latest
PORT_OUT?=5001

docker-build:
	docker build -t $(IMG):$(TAG) .

docker-run:
	docker run --rm -p $(PORT_OUT):$(PORT) --env-file .env $(IMG):$(TAG)

docker-shell:
	docker run --rm -it -p $(PORT_OUT):$(PORT) --env-file .env $(IMG):$(TAG) /bin/bash

docker-push:
	@if [ -z "$(REGISTRY)" ]; then echo "Set REGISTRY=your_registry"; exit 1; fi
	docker tag $(IMG):$(TAG) $(REGISTRY)/$(IMG):$(TAG)
	docker push $(REGISTRY)/$(IMG):$(TAG)
