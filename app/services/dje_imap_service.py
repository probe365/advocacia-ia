import email
import imaplib
import logging
import os
from datetime import datetime
from email.header import decode_header
from typing import Any, Dict, List, Optional, Tuple

from cadastro_manager import CadastroManager
from app.services.dje_service import DjeService

logger = logging.getLogger(__name__)


class DjeImapService:
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or os.getenv("DEFAULT_TENANT_ID", "public")
        self.manager = CadastroManager(self.tenant_id)
        self.dje_service = DjeService(self.manager)

    # ---------------------------------------------------------
    # Configuração
    # ---------------------------------------------------------

    def _imap_cfg(self) -> Dict[str, Any]:
        return {
            "host": os.getenv("IMAP_HOST"),
            "port": int(os.getenv("IMAP_PORT", "993")),
            "user": os.getenv("IMAP_USER"),
            "password": os.getenv("IMAP_PASSWORD"),
            "mailbox": os.getenv("IMAP_MAILBOX", "INBOX"),
            "ssl": os.getenv("IMAP_SSL", "true").lower() == "true",
            "processed_mailbox": os.getenv("IMAP_PROCESSED_MAILBOX"),
            "use_unseen": os.getenv("IMAP_USE_UNSEEN", "true").lower() == "true",
        }

    # ---------------------------------------------------------
    # Sincronização IMAP
    # ---------------------------------------------------------

    def sync(self) -> Dict[str, Any]:
        cfg = self._imap_cfg()
        if not cfg.get("host") or not cfg.get("user") or not cfg.get("password"):
            return {"status": "error", "message": "IMAP não configurado", "processed": 0}

        mailbox = cfg.get("mailbox")
        processed = 0
        last_uid = self.manager.get_inbox_state(self.tenant_id, mailbox)

        try:
            client = (
                imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
                if cfg["ssl"]
                else imaplib.IMAP4(cfg["host"], cfg["port"])
            )

            client.login(cfg["user"], cfg["password"])
            client.select(mailbox)

            # Estratégia de busca
            if cfg.get("use_unseen"):
                search_query = "UNSEEN"
            elif last_uid:
                search_query = f"UID {int(last_uid) + 1}:*"
            else:
                search_query = "ALL"

            status, data = client.uid("SEARCH", None, search_query)
            if status != "OK":
                return {"status": "error", "message": "Falha ao buscar emails", "processed": 0}

            uids = [uid for uid in data[0].split() if uid]

            for uid in uids:
                status, msg_data = client.uid("FETCH", uid, "(RFC822)")
                if status != "OK" or not msg_data:
                    continue

                raw_msg = msg_data[0][1]
                parsed = email.message_from_bytes(raw_msg)

                payload = self._extract_payload(parsed)
                stored, _ = self.dje_service.ingest_email_payload(payload)
                if stored:
                    processed += 1

                last_uid = int(uid)

                # Mover para pasta processada
                processed_mailbox = cfg.get("processed_mailbox")
                if processed_mailbox:
                    try:
                        client.uid("COPY", uid, processed_mailbox)
                        client.uid("STORE", uid, "+FLAGS", "(\\Deleted)")
                    except Exception:
                        logger.warning("Falha ao mover e-mail para pasta processada")

            if cfg.get("processed_mailbox"):
                client.expunge()

            if last_uid:
                self.manager.update_inbox_state(self.tenant_id, mailbox, last_uid)

            client.logout()
            return {"status": "ok", "message": "Sincronizado", "processed": processed}

        except Exception as exc:
            logger.exception("Erro ao sincronizar IMAP")
            return {"status": "error", "message": str(exc), "processed": processed}

    # ---------------------------------------------------------
    # Extração de payload
    # ---------------------------------------------------------

    def _extract_payload(self, msg: email.message.Message) -> Dict[str, Any]:
        subject = self._decode_header(msg.get("Subject"))
        sender = self._decode_header(msg.get("From"))
        recipients = self._decode_header(msg.get("To"))
        message_id = msg.get("Message-Id") or msg.get("Message-ID")
        date_str = msg.get("Date")
        received_at = self._parse_date(date_str)

        body_text = ""
        body_html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition") or "")

                if "attachment" in content_disposition.lower():
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                charset = part.get_content_charset() or "utf-8"

                try:
                    decoded = payload.decode(charset, errors="ignore")
                except Exception:
                    try:
                        decoded = payload.decode("utf-8", errors="ignore")
                    except Exception:
                        decoded = payload.decode("latin1", errors="ignore")

                if content_type == "text/plain" and not body_text:
                    body_text = decoded
                elif content_type == "text/html" and not body_html:
                    body_html = decoded
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    body_text = payload.decode(charset, errors="ignore")
                except Exception:
                    body_text = payload.decode("utf-8", errors="ignore")

        return {
            "subject": subject,
            "from": sender,
            "to": recipients,
            "message_id": message_id,
            "date": received_at.isoformat() if received_at else None,
            "text": body_text,
            "html": body_html,
            "source": "imap",
        }

    # ---------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------

    def _decode_header(self, value: Optional[str]) -> str:
        if not value:
            return ""
        decoded_parts = decode_header(value)
        out = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    out += part.decode(encoding or "utf-8", errors="ignore")
                except Exception:
                    out += part.decode("utf-8", errors="ignore")
            else:
                out += str(part)
        return out

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = email.utils.parsedate_to_datetime(value)
            return dt
        except Exception:
            return None
