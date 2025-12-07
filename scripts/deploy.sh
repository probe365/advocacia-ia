#!/usr/bin/env bash
set -euo pipefail

# Determine project root (folder above scripts)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists (optional)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

VENV_DIR="${PROJECT_ROOT}/.venv"
PYTHON_BIN="python3"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 not found on server" >&2
  exit 1
fi

# Create virtualenv if missing
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate virtualenv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations if Alembic config is available
if [ -f alembic.ini ]; then
  echo "Running alembic upgrade"
  alembic upgrade head
fi

# Restart application service (expects SERVICE_NAME env or defaults)
SERVICE_NAME="${SERVICE_NAME:-advocacia-ia}"
if [ -n "$SERVICE_NAME" ]; then
  echo "Restarting systemd service: $SERVICE_NAME"
  sudo systemctl restart "$SERVICE_NAME" || sudo systemctl restart "$SERVICE_NAME.service"
else
  echo "SERVICE_NAME not set; skipping systemd restart"
fi

echo "Deploy script finished successfully"
