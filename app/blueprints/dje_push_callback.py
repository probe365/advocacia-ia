from flask import Blueprint, request, jsonify, g
from app.services.dje_service import DjeService
from cadastro_manager import CadastroManager
import logging

logger = logging.getLogger(__name__)

bp_dje_push = Blueprint("dje_push", __name__, url_prefix="/api/dje/push")


@bp_dje_push.before_request
def load_tenant():
    """
    Se você usa multi-tenant por header, cookie ou domínio,
    ajuste aqui. Por enquanto, usa o tenant padrão.
    """
    g.tenant_id = request.headers.get("X-Tenant-ID") or "public"


@bp_dje_push.route("/callback", methods=["POST"])
def dje_push_callback():
    try:
        payload = request.get_json(silent=True)

        if not payload:
            logger.warning("DJE PUSH: payload vazio recebido")
            return jsonify({"status": "ignored", "message": "payload vazio"}), 200

        mgr = CadastroManager(getattr(g, "tenant_id", None))
        service = DjeService(mgr)

        stored, msg = service.ingest_push_payload(payload)

        logger.info(
            f"DJE PUSH callback recebido | tenant={g.tenant_id} | armazenados={stored}"
        )

        return jsonify({"status": "ok", "stored": stored, "message": msg}), 200

    except Exception as exc:
        logger.exception("Erro no callback do DJE PUSH")
        return jsonify({"status": "error", "message": str(exc)}), 500
