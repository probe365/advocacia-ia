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

# Prod servers keep secrets in .env.systemd, so load it when available
if [ -f .env.systemd ]; thensudo -u postgres psql -d advocacia_ia_prod <<'SQL'
-- create the sequence if it isn't there yet
CREATE SEQUENCE IF NOT EXISTS documentos_id_seq;

CREATE TABLE IF NOT EXISTS public.documentos (
    id integer NOT NULL DEFAULT nextval('documentos_id_seq'::regclass),
    tenant_id text NOT NULL,
    id_cliente varchar(50) NOT NULL,
    id_processo varchar(50) NOT NULL,
    tipo varchar(20) NOT NULL,
    titulo varchar(255) NOT NULL,
    descricao text,
    arquivo_nome varchar(255) NOT NULL,
    mime_type varchar(100),
    tamanho_bytes bigint,
    storage_backend varchar(50) NOT NULL DEFAULT 'local',
    storage_path varchar(500) NOT NULL,
    checksum_sha256 varchar(64),
    criado_por_id integer NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT fk_documentos_clientes FOREIGN KEY (id_cliente) REFERENCES public.clientes (id_cliente),
    CONSTRAINT fk_documentos_processos FOREIGN KEY (id_processo) REFERENCES public.processos (id_processo),
    CONSTRAINT fk_documentos_usuarios FOREIGN KEY (criado_por_id) REFERENCES public.usuarios (id)
);

CREATE INDEX IF NOT EXISTS ix_documentos_checksum ON public.documentos (checksum_sha256);
CREATE INDEX IF NOT EXISTS ix_documentos_id_cliente ON public.documentos (id_cliente);
CREATE INDEX IF NOT EXISTS ix_documentos_id_processo ON public.documentos (id_processo);
CREATE INDEX IF NOT EXISTS ix_documentos_tenant_id ON public.documentos (tenant_id);
SQL
  set -a
  # shellcheck disable=SC1091
  source .env.systemd
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
