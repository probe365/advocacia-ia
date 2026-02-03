import logging
import os
import json
from typing import Any, Dict, Optional

from flask import Blueprint, Response, g, jsonify, render_template, request
from flask_login import login_required

from app.services.dje_service import DjeService
from cadastro_manager import CadastroManager

logger = logging.getLogger(__name__)


dje_bp = Blueprint("dje", __name__, url_prefix="/dje")
service = DjeService()


def _get_tenant_id() -> str:
    return str(getattr(g, "tenant_id", None) or "public")


def _get_processo(process_id: str) -> Optional[dict]:
    mgr = CadastroManager(_get_tenant_id())
    return mgr.get_processo_by_id(process_id)


def _ensure_payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _normalize_payload_list(items: list) -> list:
    normalized = []
    for item in items or []:
        payload = _ensure_payload_dict(item.get("payload")) if isinstance(item, dict) else {}
        if isinstance(item, dict):
            item = {**item, "payload": payload}
        normalized.append(item)
    return normalized


@dje_bp.route("/ui/processos/<process_id>/push", methods=["GET"])
@login_required
def push_panel(process_id: str):
    processo = _get_processo(process_id)
    if not processo:
        return render_template("partials/dje_push_panel.html", processo=None)

    mgr = CadastroManager(_get_tenant_id())
    subscription = mgr.get_dje_push_subscription(process_id)
    events = _normalize_payload_list(mgr.list_dje_push_events(process_id, limit=100))
    process_number = processo.get("numero_cnj")
    emails = mgr.list_dje_email_messages(process_number, limit=50) if process_number else []
    return render_template(
        "partials/dje_push_panel.html",
        processo=processo,
        subscription=subscription,
        events=events,
        emails=emails,
    )


@dje_bp.route("/ui/processos/<process_id>/push/subscribe", methods=["POST"])
@login_required
def push_subscribe(process_id: str):
    processo = _get_processo(process_id)
    message = ""
    status = "success"
    if not processo:
        message = "Processo não encontrado."
        status = "danger"
    else:
        cnj_number = processo.get("numero_cnj")
        if not cnj_number:
            message = "Número CNJ não informado no processo."
            status = "warning"
        else:
            ok, msg = service.subscribe_push(process_id, str(cnj_number))
            message = msg
            status = "success" if ok else "danger"

    mgr = CadastroManager(_get_tenant_id())
    subscription = mgr.get_dje_push_subscription(process_id)
    events = _normalize_payload_list(mgr.list_dje_push_events(process_id, limit=100))
    process_number = processo.get("numero_cnj") if processo else None
    emails = mgr.list_dje_email_messages(process_number, limit=50) if process_number else []
    return render_template(
        "partials/dje_push_panel.html",
        processo=processo,
        subscription=subscription,
        events=events,
        emails=emails,
        message=message,
        message_status=status,
    )


@dje_bp.route("/ui/processos/<process_id>/push/sync", methods=["POST"])
@login_required
def push_sync(process_id: str):
    processo = _get_processo(process_id)
    message = ""
    status = "success"
    if not processo:
        message = "Processo não encontrado."
        status = "danger"
    else:
        cnj_number = processo.get("numero_cnj")
        if not cnj_number:
            message = "Número CNJ não informado no processo."
            status = "warning"
        else:
            ok, msg, stored = service.sync_push_events(process_id, str(cnj_number))
            message = f"{msg} ({stored} novos)." if ok else msg
            status = "success" if ok else "danger"

    mgr = CadastroManager(_get_tenant_id())
    subscription = mgr.get_dje_push_subscription(process_id)
    events = _normalize_payload_list(mgr.list_dje_push_events(process_id, limit=100))
    process_number = processo.get("numero_cnj") if processo else None
    emails = mgr.list_dje_email_messages(process_number, limit=50) if process_number else []
    return render_template(
        "partials/dje_push_panel.html",
        processo=processo,
        subscription=subscription,
        events=events,
        emails=emails,
        message=message,
        message_status=status,
    )


@dje_bp.route("/ui/processos/<process_id>/andamentos", methods=["GET"])
@login_required
def andamentos_panel(process_id: str):
    processo = _get_processo(process_id)
    if not processo:
        return render_template("partials/dje_andamentos_panel.html", processo=None)

    mgr = CadastroManager(_get_tenant_id())
    andamentos = _normalize_payload_list(mgr.list_dje_andamentos(process_id, limit=150))
    return render_template(
        "partials/dje_andamentos_panel.html",
        processo=processo,
        andamentos=andamentos,
    )


@dje_bp.route("/ui/processos/<process_id>/andamentos/sync", methods=["POST"])
@login_required
def andamentos_sync(process_id: str):
    processo = _get_processo(process_id)
    message = ""
    status = "success"
    if not processo:
        message = "Processo não encontrado."
        status = "danger"
    else:
        cnj_number = processo.get("numero_cnj")
        if not cnj_number:
            message = "Número CNJ não informado no processo."
            status = "warning"
        else:
            ok, msg, stored = service.sync_andamentos(process_id, str(cnj_number))
            message = f"{msg} ({stored} novos)." if ok else msg
            status = "success" if ok else "danger"

    mgr = CadastroManager(_get_tenant_id())
    andamentos = _normalize_payload_list(mgr.list_dje_andamentos(process_id, limit=150))
    return render_template(
        "partials/dje_andamentos_panel.html",
        processo=processo,
        andamentos=andamentos,
        message=message,
        message_status=status,
    )


@dje_bp.route("/ui/processos/<process_id>/push/inteiro-teor/<int:event_id>", methods=["GET"])
@login_required
def inteiro_teor(process_id: str, event_id: int):
    processo = _get_processo(process_id)
    if not processo:
        return Response("Processo não encontrado", status=404)

    mgr = CadastroManager(_get_tenant_id())
    event = mgr.get_dje_push_event_by_id(process_id, event_id)
    if not event:
        return Response("Evento não encontrado", status=404)

    payload = _ensure_payload_dict(event.get("payload"))
    comunicacao = (
        payload.get("numeroComunicacao")
        or payload.get("idComunicacao")
        or payload.get("numero_comunicacao")
        or payload.get("id_comunicacao")
        or event.get("external_id")
    )
    if not comunicacao:
        return Response("Número de comunicação ausente", status=400)

    cnj_number = event.get("cnj_number") or processo.get("numero_cnj")
    if not cnj_number:
        return Response("Número CNJ ausente", status=400)

    ok, content, msg, content_type = service.fetch_inteiro_teor(str(cnj_number), str(comunicacao))
    if not ok:
        return Response(msg or "Falha ao obter inteiro teor", status=502)

    return Response(content, content_type=content_type or "application/pdf")


@dje_bp.route("/webhook/push", methods=["POST"])
def push_webhook():
    expected = os.getenv("DJE_WEBHOOK_SECRET")
    provided = request.headers.get("X-DJE-Webhook-Secret") or request.headers.get("Authorization")
    if expected and expected not in (provided or ""):
        return jsonify({"status": "unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    stored, msg = service.ingest_push_payload(payload)
    status = "ok" if stored >= 0 else "error"
    return jsonify({"status": status, "stored": stored, "message": msg})


@dje_bp.route("/webhook/email", methods=["POST"])
def email_webhook():
    expected = os.getenv("DJE_EMAIL_WEBHOOK_SECRET")
    provided = request.headers.get("X-DJE-Email-Secret") or request.headers.get("Authorization")
    if expected and expected not in (provided or ""):
        return jsonify({"status": "unauthorized"}), 401

    payload = request.get_json(silent=True) or request.form.to_dict() or {}
    stored, msg = service.ingest_email_payload(payload)
    status = "ok" if stored >= 0 else "error"
    return jsonify({"status": status, "stored": stored, "message": msg})
