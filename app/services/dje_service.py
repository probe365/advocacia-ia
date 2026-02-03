import hashlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import current_app, g

from cadastro_manager import CadastroManager

logger = logging.getLogger(__name__)


class DjeService:
    """
    Serviço responsável EXCLUSIVAMENTE pelo módulo PUSH DJE:
    - Push CNJ (webhook e sincronização manual)
    - Push TJSP (via e-mail)
    - Inteiro teor via CNJ
    """

    def __init__(self, manager: Optional[CadastroManager] = None):
        self._manager_override = manager
        self._cached_token = None
        self._cached_token_exp = None


    def _get_manager(self) -> CadastroManager:
        if self._manager_override:
            return self._manager_override
        return CadastroManager(getattr(g, "tenant_id", None))

    # ---------------------------------------------------------
    # Configuração
    # ---------------------------------------------------------

    

    # ---------------------------------------------------------
    # TOKEN OAUTH2 COM CACHE
    # ---------------------------------------------------------

    def _get_oauth_token(self):
        # Se já existe token válido em cache, usa ele
        if self._cached_token and self._cached_token_exp:
            if datetime.utcnow() < self._cached_token_exp:
                return self._cached_token

        cfg = self._cfg()

        data = {
            "grant_type": "client_credentials",
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "scope": "openid"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        resp = requests.post(cfg["token"], data=data, headers=headers, timeout=20)

        if resp.status_code != 200:
            raise Exception(f"Erro ao obter token OAuth2: {resp.text}")

        token = resp.json()["access_token"]
        expires = resp.json().get("expires_in", 300)

        # Guarda token no cache e define expiração com margem de segurança
        self._cached_token = token
        self._cached_token_exp = datetime.utcnow() + timedelta(seconds=expires - 60)

        return token


    def _cfg(self) -> Dict[str, Any]:
        cfg = {}
        try:
            app_cfg = current_app.config
            cfg = {
                "base_url": app_cfg.get("DJE_BASE_URL"),
                "api_key": app_cfg.get("DJE_API_KEY"),
                "token": app_cfg.get("DJE_TOKEN"),
                "client_id": app_cfg.get("DJE_CLIENT_ID"),
                "client_secret": app_cfg.get("DJE_CLIENT_SECRET"),
                "push_subscribe_path": app_cfg.get("DJE_PUSH_SUBSCRIBE_PATH"),
                "push_events_path": app_cfg.get("DJE_PUSH_EVENTS_PATH"),
                "inteiro_teor_path": app_cfg.get("DJE_INTEIRO_TEOR_PATH"),
                "push_callback_url": app_cfg.get("DJE_PUSH_CALLBACK_URL"),
                "timeout": app_cfg.get("DJE_TIMEOUT", 20),
            }
        except Exception:
            cfg = {}

        return {
            "base_url": cfg.get("base_url") or os.getenv("DJE_BASE_URL", "https://gateway.cloud.pje.jus.br/domicilio-eletronico"),
            "api_key": cfg.get("api_key") or os.getenv("DJE_API_KEY"),
            "token": None,
            "client_id": cfg.get("client_id") or os.getenv("DJE_CLIENT_ID"),
            "client_secret": cfg.get("client_secret") or os.getenv("DJE_CLIENT_SECRET"),
            "push_subscribe_path": cfg.get("push_subscribe_path") or os.getenv("DJE_PUSH_SUBSCRIBE_PATH"),
            "push_events_path": cfg.get("push_events_path") or os.getenv("DJE_PUSH_EVENTS_PATH"),
            "inteiro_teor_path": cfg.get("inteiro_teor_path") or os.getenv("DJE_INTEIRO_TEOR_PATH"),
            "push_callback_url": cfg.get("push_callback_url") or os.getenv("DJE_PUSH_CALLBACK_URL"),
            "timeout": cfg.get("timeout") or int(os.getenv("DJE_TIMEOUT", "20")),
        }

    def _headers(self):
        token = self._get_oauth_token()
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }




    def _build_url(self, path: str) -> str:
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = self._cfg()["base_url"].rstrip("/")
        return f"{base}/{path.lstrip('/')}"

    # ---------------------------------------------------------
    # HTTP
    # ---------------------------------------------------------

    def _request(self, method: str, path: str, *, params=None, payload=None) -> Tuple[bool, Any, str]:
        url = self._build_url(path)
        if not url:
            return False, None, "Endpoint não configurado."

        try:
            if method == "FORM":
                response = requests.post(
                    url,
                    headers=self._headers(),
                    data=payload,
                    timeout=self._cfg()["timeout"],
                )
            else:
                response = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    params=params,
                    json=payload,
                    timeout=self._cfg()["timeout"],
                )

            if response.status_code >= 400:
                return False, None, f"Erro {response.status_code}: {response.text}"

            if response.text:
                return True, response.json(), ""

            return True, None, ""

        except Exception as exc:
            logger.exception("Erro ao chamar DJE API")
            return False, None, str(exc)

    def _request_raw(self, method: str, path: str, *, params=None, payload=None):
        url = self._build_url(path)
        if not url:
            return False, b"", "Endpoint não configurado.", None

        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=payload,
                timeout=self._cfg()["timeout"],
            )

            if response.status_code >= 400:
                return False, b"", f"Erro {response.status_code}: {response.text}", response.headers.get("Content-Type")

            return True, response.content or b"", "", response.headers.get("Content-Type")

        except Exception as exc:
            logger.exception("Erro ao chamar DJE API")
            return False, b"", str(exc), None

    # ---------------------------------------------------------
    # PUSH CNJ
    # ---------------------------------------------------------

    def subscribe_push(self, process_id: str, cnj_number: str) -> Tuple[bool, str]:
        cfg = self._cfg()
        if not cfg.get("push_subscribe_path"):
            return False, "Defina DJE_PUSH_SUBSCRIBE_PATH para ativar a assinatura."

        payload = {
            "numeroProcesso": cnj_number,
            "processId": process_id,
            "callbackUrl": cfg.get("push_callback_url"),
        }

        ok, data, msg = self._request("POST", cfg["push_subscribe_path"], payload=payload)
        if not ok:
            return False, msg

        external_id = None
        status = None

        if isinstance(data, dict):
            external_id = data.get("id") or data.get("subscriptionId") or data.get("uuid")
            status = data.get("status") or data.get("state")

        self._get_manager().upsert_dje_push_subscription(
            process_id=process_id,
            cnj_number=cnj_number,
            enabled=True,
            webhook_url=cfg.get("push_callback_url"),
            external_id=external_id,
            status=status,
        )

        return True, "Assinatura registrada com sucesso."

    def sync_push_events(self, process_id: str, cnj_number: str) -> Tuple[bool, str, int]:
        cfg = self._cfg()
        if not cfg.get("push_events_path"):
            return False, "Defina DJE_PUSH_EVENTS_PATH para sincronizar eventos.", 0

        ok, data, msg = self._request("GET", cfg["push_events_path"], params={"numeroProcesso": cnj_number})
        if not ok:
            return False, msg, 0

        events = self._normalize_push_events(data)
        stored = self._get_manager().insert_dje_push_events(process_id, cnj_number, events)
        self._get_manager().update_dje_push_subscription_sync(process_id, datetime.utcnow())

        return True, "Eventos sincronizados.", stored

    # ---------------------------------------------------------
    # Webhook CNJ
    # ---------------------------------------------------------

    def ingest_push_payload(self, payload: Any) -> Tuple[int, str]:
        if not payload:
            return 0, "Payload vazio."

        cnj_number = None
        if isinstance(payload, dict):
            cnj_number = (
                payload.get("numeroProcesso")
                or payload.get("cnj")
                or payload.get("processo")
            )

        if not cnj_number:
            return 0, "Número CNJ não encontrado no payload."

        mgr = self._get_manager()
        processo = mgr.get_processo_by_cnj(str(cnj_number))

        if not processo:
            return 0, "Processo não encontrado para o número CNJ informado."

        process_id = str(processo.get("id_processo"))

        events = self._normalize_push_events(payload)
        stored = mgr.insert_dje_push_events(process_id, str(cnj_number), events)
        mgr.update_dje_push_subscription_sync(process_id, datetime.utcnow())

        return stored, "Eventos recebidos."

    # ---------------------------------------------------------
    # Inteiro Teor
    # ---------------------------------------------------------

    def fetch_inteiro_teor(self, cnj_number: str, comunicacao: str):
        cfg = self._cfg()
        path = cfg.get("inteiro_teor_path") or os.getenv("DJE_INTEIRO_TEOR_PATH")

        if not path:
            return False, b"", "Defina DJE_INTEIRO_TEOR_PATH para obter o inteiro teor.", None

        path = (
            path.replace("{numeroProcesso}", str(cnj_number))
                .replace("{numeroComunicacao}", str(comunicacao))
        )

        # Alguns tribunais aceitam GET, outros PUT
        ok, content, msg, ctype = self._request_raw("GET", path)
        if ok:
            return ok, content, msg, ctype

        return self._request_raw("PUT", path)

    # ---------------------------------------------------------
    # Normalização de eventos PUSH
    # ---------------------------------------------------------

    def _normalize_push_events(self, data: Any) -> List[Dict[str, Any]]:
        items = self._extract_items(data)
        results = []

        for item in items:
            if not isinstance(item, dict):
                continue

            event_type = self._infer_event_type(item)
            title = (
                item.get("titulo")
                or item.get("descricao")
                or item.get("assunto")
                or event_type
            )

            event_date = self._parse_date(
                item.get("data")
                or item.get("dataEvento")
                or item.get("data_evento")
                or item.get("dataHora")
                or item.get("data_hora")
            )

            prazo_final = self._parse_date(
                item.get("prazoFinal")
                or item.get("prazo_final")
                or item.get("dataPrazo")
            )

            status_ciencia = (
                item.get("statusCiencia")
                or item.get("status_ciencia")
                or item.get("ciencia")
            )

            external_id = (
                item.get("id")
                or item.get("idNotificacao")
                or item.get("uuid")
            )

            event_hash = self._hash_payload(item)

            results.append({
                "event_type": event_type,
                "event_title": title,
                "event_date": event_date,
                "prazo_final": prazo_final,
                "status_ciencia": status_ciencia,
                "external_id": external_id,
                "payload": item,
                "event_hash": event_hash,
                "origem": "djecnj",
            })

        # Caso o payload seja um único objeto
        if not results and isinstance(data, dict):
            event_hash = self._hash_payload(data)
            results.append({
                "event_type": self._infer_event_type(data),
                "event_title": data.get("titulo") or data.get("descricao") or "evento",
                "event_date": self._parse_date(data.get("data") or data.get("dataHora")),
                "prazo_final": self._parse_date(data.get("prazoFinal")),
                "status_ciencia": data.get("statusCiencia") or data.get("status_ciencia") or data.get("ciencia"),
                "external_id": data.get("id") or data.get("uuid"),
                "payload": data,
                "event_hash": event_hash,
                "origem": "djecnj",
            })

        return results

    # ---------------------------------------------------------
    # E-mail TJSP
    # ---------------------------------------------------------

    def ingest_email_payload(self, payload: Any) -> Tuple[int, str]:
        data = payload if isinstance(payload, dict) else {}

        subject = data.get("subject") or data.get("assunto")
        text = data.get("text") or data.get("texto") or data.get("body_text")
        html = data.get("html") or data.get("body_html")
        message_id = (
            data.get("message_id")
            or data.get("Message-Id")
            or data.get("messageId")
        )

        received_at = self._parse_date(data.get("date") or data.get("received_at"))

        process_number = (
            self._extract_cnj(subject or "")
            or self._extract_cnj(text or "")
            or self._extract_cnj(html or "")
        )

        movement_at = (
            self._extract_movement_at(subject or "")
            or self._extract_movement_at(text or "")
        )

        dedupe_hash = self._build_dedupe_hash(message_id, subject, text, html)

        stored = self._get_manager().insert_dje_email_message(
            message_uuid=str(uuid.uuid4()),
            process_number=process_number,
            source=data.get("source") or "tjsp_push",
            movement_at=movement_at or received_at,
            subject=subject,
            body_text=(text or "").strip() or None,
            body_html=(html or "").strip() or None,
            message_id=message_id,
            dedupe_hash=dedupe_hash,
        )

        return stored, "Email processado."

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _extract_items(self, data: Any) -> List[Any]:
        if data is None:
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in (
                "items",
                "data",
                "results",
                "content",
                "notificacoes",
                "eventos",
                "movimentos",
            ):
                value = data.get(key)
                if isinstance(value, list):
                    return value

        return []

    def _infer_event_type(self, item: Dict[str, Any]) -> str:
        raw = " ".join(
            str(item.get(k, ""))
            for k in ("tipo", "type", "categoria", "titulo", "descricao", "assunto")
        ).lower()

        if "citação" in raw or "citacao" in raw:
            return "citacao"
        if "intima" in raw:
            return "intimacao"
        if "inteiro" in raw and "teor" in raw:
            return "inteiro_teor"
        if "ciência" in raw or "ciencia" in raw:
            return "status_ciencia"

        return item.get("tipo") or item.get("type") or "evento"

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            try:
                return datetime.utcfromtimestamp(float(value))
            except Exception:
                return None

        if isinstance(value, str):
            raw = value.strip()

            # ISO com Z
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"

            # ISO
            try:
                return datetime.fromisoformat(raw)
            except Exception:
                pass

            # dd/mm/yyyy
            try:
                return datetime.strptime(raw, "%d/%m/%Y")
            except Exception:
                pass

            # dd/mm/yyyy HH:MM
            try:
                return datetime.strptime(raw, "%d/%m/%Y %H:%M")
            except Exception:
                pass

        return None

    def _extract_cnj(self, text: str) -> Optional[str]:
        if not text:
            return None

        match = re.search(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", text)
        if match:
            return match.group(0)

        digits = re.sub(r"\D", "", text)
        if len(digits) >= 20:
            return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:20]}"

        return None

    def _extract_movement_at(self, text: str) -> Optional[datetime]:
        if not text:
            return None

        match = re.search(r"(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}))?", text)
        if not match:
            return None

        date_part = match.group(1)
        time_part = match.group(2) or "00:00"

        try:
            return datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
        except Exception:
            return None

    def _hash_payload(self, payload: Any) -> str:
        try:
            raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            raw = str(payload)

        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _build_dedupe_hash(
        self,
        message_id: Optional[str],
        subject: Optional[str],
        text: Optional[str],
        html: Optional[str],
    ) -> str:
        base = message_id or ""
        if not base:
            base = f"{subject or ''}|{(text or '')[:300]}|{(html or '')[:300]}"
        return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()
