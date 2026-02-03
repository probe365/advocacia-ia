from flask import Blueprint, request, jsonify
from app.services.dje_service import DjeService

callback_bp = Blueprint("callback", __name__)

@callback_bp.route("/api/dje/push/callback", methods=["POST"])
def dje_push_callback():
    payload = request.get_json(silent=True) or {}
    stored, msg = DjeService().ingest_push_payload(payload)
    return jsonify({"status": "ok", "stored": stored, "message": msg}), 200
