# cadastro_manager.py (Versão Final e Completa para PostgreSQL)
import os
import psycopg2
from psycopg2 import extensions as _psycopg2_extensions
from psycopg2.extras import RealDictCursor
from typing import Any, Dict, List, Optional, Tuple, Literal, cast
import uuid
from datetime import datetime
import json
import logging
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv(override=True)
logger = logging.getLogger(__name__)

FetchMode = Literal["one", "all"]
Params = Tuple[Any, ...]


class CadastroManager:
    """
    Gerencia todos os dados cadastrais em um banco de dados PostgreSQL.
    Suporte multi-tenant simples via coluna tenant_id (quando habilitado).
    """

    # Wrappers de compatibilidade (recomendado)
    def fetch_all(self, query: str, params: Params = ()) -> List[Dict[str, Any]]:
        return self._execute_query(query, params, fetch="all") or []

    def fetch_one(self, query: str, params: Params = ()) -> Optional[Dict[str, Any]]:
        return self._execute_query(query, params, fetch="one")

    def execute_sql(self, query: str, params: Params = ()) -> int:
        return self._execute_query(query, params)



    def get_escritorio_info(self):
        """Retorna os dados do escritório do tenant atual."""
        query = "SELECT * FROM escritorio WHERE tenant_id = %s"
        return self._execute_query(query, (self.tenant_id,), fetch="one")

    def get_advogados(self):
        """Retorna todos os advogados do tenant atual."""
        query = "SELECT * FROM advogados WHERE tenant_id = %s"
        return self._execute_query(query, (self.tenant_id,), fetch="all")



    def get_clientes(self) -> List[Dict[str, Any]]:
        """Retorna todos os clientes do tenant atual."""
        where_sql, params = self._with_tenant_where("", cast(Params, ()))
        query = f"SELECT * FROM clientes {where_sql} ORDER BY nome_completo"
        return self._execute_query(query, params, fetch="all")
    
    def upsert_process_firac(
        self,
        *,
        process_id: str,
        facts: str = "",
        issue: str = "",
        rules: str = "",
        application: str = "",
        conclusion: str = "",
        created_by_user_id: Optional[int] = None,
        source: str = "ui",
    ) -> None:
        # fallback sem depender de constraint UNIQUE
        rowcount = self._execute_query(
            """
            UPDATE process_firac
                 SET facts = %s,
                         issue = %s,
                         rules = %s,
                         application = %s,
                         conclusion = %s,
                         source = %s,
                         created_by_user_id = COALESCE(%s, created_by_user_id),
                         updated_at = CURRENT_TIMESTAMP
             WHERE tenant_id = %s AND process_id = %s AND source = %s
            """,
            (
                facts or "",
                issue or "",
                rules or "",
                application or "",
                conclusion or "",
                source or "ui",
                int(created_by_user_id) if created_by_user_id is not None else None,
                str(self.tenant_id),
                str(process_id),
                source or "ui",
            ),
            fetch=None,
        )

        if rowcount and int(rowcount) > 0:
            return

        self._execute_query(
            """
            INSERT INTO process_firac
                (tenant_id, process_id, facts, issue, rules, application, conclusion, source, created_by_user_id)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(self.tenant_id),
                str(process_id),
                facts or "",
                issue or "",
                rules or "",
                application or "",
                conclusion or "",
                source or "ui",
                int(created_by_user_id) if created_by_user_id is not None else None,
            ),
            fetch=None,
        )

    def get_process_firac(self, process_id: str) -> Optional[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT tenant_id, process_id, facts, issue, rules, application, conclusion, source, created_at, updated_at
            FROM process_firac
            WHERE tenant_id = %s AND process_id = %s
            LIMIT 1
            """,
            (str(self.tenant_id), str(process_id)),
            fetch="one",
        )

    # ---------- DJE / CNJ (Push & Andamentos) ----------
    def get_dje_push_subscription(self, process_id: str) -> Optional[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, cnj_number, external_id, webhook_url,
                   enabled, status, last_sync_at, created_at, updated_at
            FROM dje_push_subscriptions
            WHERE tenant_id = %s AND process_id = %s
            LIMIT 1
            """,
            (str(self.tenant_id), str(process_id)),
            fetch="one",
        )

    def upsert_dje_push_subscription(
        self,
        *,
        process_id: str,
        cnj_number: str,
        enabled: bool = True,
        webhook_url: Optional[str] = None,
        external_id: Optional[str] = None,
        status: Optional[str] = None,
        last_sync_at: Optional[datetime] = None,
    ) -> None:
        rowcount = self._execute_query(
            """
            UPDATE dje_push_subscriptions
               SET cnj_number = %s,
                   enabled = %s,
                   webhook_url = %s,
                   external_id = COALESCE(%s, external_id),
                   status = COALESCE(%s, status),
                   last_sync_at = %s,
                   updated_at = CURRENT_TIMESTAMP
             WHERE tenant_id = %s AND process_id = %s
            """,
            (
                str(cnj_number),
                bool(enabled),
                webhook_url,
                external_id,
                status,
                last_sync_at,
                str(self.tenant_id),
                str(process_id),
            ),
            fetch=None,
        )

        if rowcount and int(rowcount) > 0:
            return

        self._execute_query(
            """
            INSERT INTO dje_push_subscriptions
                (tenant_id, process_id, cnj_number, external_id, webhook_url, enabled, status, last_sync_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(self.tenant_id),
                str(process_id),
                str(cnj_number),
                external_id,
                webhook_url,
                bool(enabled),
                status,
                last_sync_at,
            ),
            fetch=None,
        )

    def update_dje_push_subscription_sync(self, process_id: str, last_sync_at: Optional[datetime]) -> None:
        self._execute_query(
            """
            UPDATE dje_push_subscriptions
               SET last_sync_at = %s,
                   updated_at = CURRENT_TIMESTAMP
             WHERE tenant_id = %s AND process_id = %s
            """,
            (last_sync_at, str(self.tenant_id), str(process_id)),
            fetch=None,
        )

    def insert_dje_push_events(self, process_id: str, cnj_number: str, events: List[Dict[str, Any]]) -> int:
        stored = 0
        for event in events:
            rowcount = self._execute_query(
                """
                INSERT INTO dje_push_events
                    (tenant_id, process_id, cnj_number, event_type, event_title,
                     event_date, prazo_final, status_ciencia, external_id,
                     payload, event_hash, origem)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, process_id, event_hash) DO NOTHING
                """,
                (
                    str(self.tenant_id),
                    str(process_id),
                    str(cnj_number),
                    event.get("event_type"),
                    event.get("event_title"),
                    event.get("event_date"),
                    event.get("prazo_final"),
                    event.get("status_ciencia"),
                    event.get("external_id"),
                    json.dumps(event.get("payload", {}), ensure_ascii=False, default=str),
                    event.get("event_hash"),
                    event.get("origem") or "djecnj",
                ),
                fetch=None,
            )
            if rowcount and int(rowcount) > 0:
                stored += 1
        return stored

    def list_dje_push_events(self, process_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, cnj_number, event_type, event_title,
                   event_date, prazo_final, status_ciencia, external_id, payload, origem, created_at
            FROM dje_push_events
            WHERE tenant_id = %s AND process_id = %s
            ORDER BY event_date DESC NULLS LAST, created_at DESC
            LIMIT %s
            """,
            (str(self.tenant_id), str(process_id), int(limit)),
            fetch="all",
        )

    def get_dje_push_event_by_id(self, process_id: str, event_id: int) -> Optional[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, cnj_number, event_type, event_title,
                   event_date, prazo_final, status_ciencia, external_id, payload, origem, created_at
            FROM dje_push_events
            WHERE tenant_id = %s AND process_id = %s AND id = %s
            LIMIT 1
            """,
            (str(self.tenant_id), str(process_id), int(event_id)),
            fetch="one",
        )

    def insert_dje_andamentos(self, process_id: str, cnj_number: str, items: List[Dict[str, Any]]) -> int:
        stored = 0
        for item in items:
            rowcount = self._execute_query(
                """
                INSERT INTO dje_andamentos
                    (tenant_id, process_id, cnj_number, movimento_data, descricao,
                     tipo_comunicacao, tribunal, orgao, grau, external_id, payload, event_hash, origem)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, process_id, event_hash) DO NOTHING
                """,
                (
                    str(self.tenant_id),
                    str(process_id),
                    str(cnj_number),
                    item.get("movimento_data"),
                    item.get("descricao"),
                    item.get("tipo_comunicacao"),
                    item.get("tribunal"),
                    item.get("orgao"),
                    item.get("grau"),
                    item.get("external_id"),
                    json.dumps(item.get("payload", {}), ensure_ascii=False, default=str),
                    item.get("event_hash"),
                    item.get("origem") or "djecnj",
                ),
                fetch=None,
            )
            if rowcount and int(rowcount) > 0:
                stored += 1
        return stored

    def list_dje_andamentos(self, process_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, cnj_number, movimento_data, descricao, tipo_comunicacao,
                   tribunal, orgao, grau, external_id, payload, origem, created_at
            FROM dje_andamentos
            WHERE tenant_id = %s AND process_id = %s
            ORDER BY movimento_data DESC NULLS LAST, created_at DESC
            LIMIT %s
            """,
            (str(self.tenant_id), str(process_id), int(limit)),
            fetch="all",
        )

    def insert_dje_email_message(
        self,
        *,
        message_uuid: str,
        process_number: Optional[str],
        source: Optional[str],
        movement_at: Optional[datetime],
        subject: Optional[str],
        body_text: Optional[str],
        body_html: Optional[str],
        message_id: Optional[str],
        dedupe_hash: str,
    ) -> int:
        rowcount = self._execute_query(
            """
            INSERT INTO dje_email_messages
                (id, tenant_id, process_number, source, movement_at, subject,
                body_text, body_html, message_id, dedupe_hash)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, dedupe_hash) DO NOTHING
            """,
            (
                message_uuid,
                str(self.tenant_id),
                str(process_number) if process_number else None,
                source,
                movement_at,
                subject,
                body_text,
                body_html,
                message_id,
                dedupe_hash,
            ),
            fetch=None,
        )
        return int(rowcount or 0)

    def list_dje_email_messages(self, process_number: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_number, source, movement_at, subject,
                   body_text, body_html, message_id, dedupe_hash, created_at
            FROM dje_email_messages
            WHERE tenant_id = %s AND process_number = %s
            ORDER BY movement_at DESC NULLS LAST, created_at DESC
            LIMIT %s
            """,
            (str(self.tenant_id), str(process_number), int(limit)),
            fetch="all",
        )

    def get_inbox_state(self, tenant_id: str, mailbox: str) -> Optional[int]:
        row = self._execute_query(
            """
            SELECT last_uid FROM dje_inbox_state
            WHERE tenant_id = %s AND mailbox = %s
            LIMIT 1
            """,
            (str(tenant_id), str(mailbox)),
            fetch="one",
        )
        if row and row.get("last_uid") is not None:
            return int(row.get("last_uid"))
        return None

    def update_inbox_state(self, tenant_id: str, mailbox: str, last_uid: int) -> None:
        rowcount = self._execute_query(
            """
            UPDATE dje_inbox_state
               SET last_uid = %s,
                   updated_at = CURRENT_TIMESTAMP
             WHERE tenant_id = %s AND mailbox = %s
            """,
            (int(last_uid), str(tenant_id), str(mailbox)),
            fetch=None,
        )
        if rowcount and int(rowcount) > 0:
            return

        self._execute_query(
            """
            INSERT INTO dje_inbox_state (tenant_id, mailbox, last_uid)
            VALUES (%s, %s, %s)
            """,
            (str(tenant_id), str(mailbox), int(last_uid)),
            fetch=None,
        )

    def get_processo_by_cnj(self, numero_cnj: str) -> Optional[Dict[str, Any]]:
        """
        Return a single processo record matching the given CNJ number for the current tenant.

        Args:
            numero_cnj: The CNJ (case) number to search for.

        Returns:
            A dictionary with the processo fields if found; otherwise None.
        """
        return self._execute_query(
            """
            SELECT * FROM processos
            WHERE tenant_id = %s AND numero_cnj = %s
            LIMIT 1
            """,
            (str(self.tenant_id), str(numero_cnj)),
            fetch="one",
        )


    def __init__(self, tenant_id: str | None = None, is_global_admin: bool = False):
        self._db_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        default_tenant = os.getenv("DEFAULT_TENANT_ID", "public")
        self.tenant_id = str(tenant_id) if tenant_id else default_tenant

        multi_tenant_enabled = os.getenv("MULTI_TENANT", "0") == "1"
        self.is_global_admin = is_global_admin
        self.multi_tenant = multi_tenant_enabled and not self.is_global_admin

        # Fim do __init__

        # Tabelas agora gerenciadas exclusivamente por Alembic migrations.


    def _get_db_params(self) -> Dict[str, str]:
        def _strip_inline_comment(value: Optional[str]) -> str:
            if not value:
                return ""
            # remove comentários inline do .env (ex: "senha # comentario")
            if " #" in value:
                value = value.split(" #", 1)[0]
            return value.strip()

        def _warn_non_ascii(label: str, value: str) -> None:
            try:
                value.encode("ascii")
            except UnicodeEncodeError:
                logger.warning(f"[DB PARAM] {label} contém caracteres não-ASCII. Verifique o .env.")

        dbname = _strip_inline_comment(os.getenv("DB_NAME", "advocacia_ia"))
        user = _strip_inline_comment(os.getenv("DB_USER", "postgres"))
        password = _strip_inline_comment(os.getenv("DB_PASSWORD", ""))
        host = _strip_inline_comment(os.getenv("DB_HOST", "localhost"))
        port = _strip_inline_comment(os.getenv("DB_PORT", "5432"))

        _warn_non_ascii("DB_NAME", dbname)
        _warn_non_ascii("DB_USER", user)
        _warn_non_ascii("DB_PASSWORD", password)
        _warn_non_ascii("DB_HOST", host)
        _warn_non_ascii("DB_PORT", port)

        return {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
        }


    def _get_connection(self, client_encoding: Optional[str] = None):
        params = self._get_db_params()

        # log sem expor senha
        safe_params = {k: ("***" if "password" in k.lower() else v)
                        for k, v in params.items()}
        logger.info(f"[DB CONNECT] Connecting with params: {safe_params}")
        print(f"[DEBUG] Connecting to database: {params['dbname']} on host: {params['host']} as user: {params['user']}")

        # garante que nenhum parâmetro seja bytes (evita UnicodeDecodeError no libpq)
        cleaned_params: Dict[str, str] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bytes):
                try:
                    cleaned_params[key] = value.decode("utf-8")
                except UnicodeDecodeError:
                    cleaned_params[key] = value.decode("latin1")
            else:
                cleaned_params[key] = str(value)

        # força client_encoding na conexão (evita erro ao decodificar parâmetros iniciais)
        encoding = client_encoding or os.getenv("DB_CLIENT_ENCODING")
        if encoding:
            cleaned_params["options"] = f"-c client_encoding={encoding}"

        def _clear_pg_env() -> Dict[str, str]:
            removed: Dict[str, str] = {}
            for key in list(os.environ.keys()):
                if key.upper().startswith("PG"):
                    removed[key] = os.environ.pop(key)
            if removed:
                logger.warning(f"[DB CONNECT] Removidos PG* do ambiente: {sorted(removed.keys())}")
            return removed

        def _apply_pg_overrides() -> Dict[str, Optional[str]]:
            overrides: Dict[str, Optional[str]] = {}
            # evita leitura de pgpass/pgservice em paths com caracteres não-UTF-8
            for key in ("PGPASSFILE", "PGSERVICEFILE"):
                overrides[key] = os.environ.get(key)
                os.environ[key] = os.devnull
            return overrides

        def _restore_pg_overrides(overrides: Dict[str, Optional[str]]) -> None:
            for key, prev in overrides.items():
                if prev is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = prev

        def _apply_home_overrides() -> Dict[str, Optional[str]]:
            overrides: Dict[str, Optional[str]] = {}
            # força paths ASCII para evitar decode de HOME/APPDATA pelo libpq no Windows
            safe_home = os.getcwd()
            for key in ("APPDATA", "USERPROFILE", "HOMEPATH", "HOMEDRIVE", "HOME"):
                overrides[key] = os.environ.get(key)
                os.environ[key] = safe_home
            return overrides

        def _restore_home_overrides(overrides: Dict[str, Optional[str]]) -> None:
            for key, prev in overrides.items():
                if prev is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = prev

        def _restore_pg_env(removed: Dict[str, str]) -> None:
            for key, value in removed.items():
                os.environ[key] = value

        def _connect_with_kwargs():
            removed = _clear_pg_env()
            pg_overrides = _apply_pg_overrides()
            home_overrides = _apply_home_overrides()
            try:
                return psycopg2.connect(**cleaned_params)
            finally:
                _restore_home_overrides(home_overrides)
                _restore_pg_overrides(pg_overrides)
                _restore_pg_env(removed)

        def _connect_with_dsn():
            dsn_local = _psycopg2_extensions.make_dsn(**cleaned_params)
            if isinstance(dsn_local, bytes):
                try:
                    dsn_local = dsn_local.decode("utf-8")
                except UnicodeDecodeError:
                    dsn_local = dsn_local.decode("latin1")
            else:
                dsn_local = str(dsn_local)
            removed = _clear_pg_env()
            pg_overrides = _apply_pg_overrides()
            home_overrides = _apply_home_overrides()
            try:
                return psycopg2.connect(dsn_local)
            finally:
                _restore_home_overrides(home_overrides)
                _restore_pg_overrides(pg_overrides)
                _restore_pg_env(removed)

        def _connect_with_pg8000():
            import pg8000
            return pg8000.connect(
                user=cleaned_params.get("user"),
                password=cleaned_params.get("password"),
                host=cleaned_params.get("host"),
                port=int(cleaned_params.get("port")) if cleaned_params.get("port") else None,
                database=cleaned_params.get("dbname"),
            )

        prefer_pg8000 = os.getenv("DB_USE_PG8000", "0") == "1"

        # aqui deixamos o psycopg2 cuidar de encoding/DSN
        if prefer_pg8000:
            conn = _connect_with_pg8000()
        else:
            try:
                conn = _connect_with_kwargs()
            except UnicodeDecodeError as exc:
                logger.warning(f"[DB CONNECT] UnicodeDecodeError com kwargs: {exc}. Tentando DSN.")
                try:
                    conn = _connect_with_dsn()
                except UnicodeDecodeError as exc2:
                    logger.warning(f"[DB CONNECT] UnicodeDecodeError com DSN: {exc2}. Tentando pg8000.")
                    conn = _connect_with_pg8000()
        if encoding:
            try:
                conn.set_client_encoding(encoding)
            except Exception as exc:
                logger.warning(f"[DB CONNECT] Falha ao aplicar client_encoding='{encoding}': {exc}")
        return conn



    def _execute_query(self, query: str, params: Params = (), fetch: FetchMode = None):
        """
        Executa uma query SQL parametrizada.
        Se fetch="one" retorna um dict (ou None).
        Se fetch="all" retorna uma lista de dicts.
        Caso contrário, retorna rowcount.
        """
        def _is_pg8000_conn(conn) -> bool:
            return conn.__class__.__module__.startswith("pg8000")

        def _rows_to_dicts(cur, rows):
            cols = [desc[0] for desc in (cur.description or [])]
            return [dict(zip(cols, row)) for row in rows]

        def _run_with_encoding(encoding: Optional[str]):
            with self._get_connection(client_encoding=encoding) as conn:
                if _is_pg8000_conn(conn):
                    cur = conn.cursor()
                    cur.execute(query, params)
                    if fetch == "one":
                        row = cur.fetchone()
                        if row is None:
                            return None
                        return _rows_to_dicts(cur, [row])[0]
                    if fetch == "all":
                        rows = cur.fetchall()
                        return _rows_to_dicts(cur, rows)
                    conn.commit()
                    return cur.rowcount if cur.rowcount is not None else 0
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if fetch == "one":
                        return cur.fetchone()
                    if fetch == "all":
                        return cur.fetchall()
                    conn.commit()
                    return cur.rowcount

        primary_encoding = os.getenv("DB_CLIENT_ENCODING")
        fallback_encoding = os.getenv("DB_CLIENT_ENCODING_FALLBACK", "LATIN1")

        try:
            return _run_with_encoding(primary_encoding)
        except UnicodeDecodeError as exc:
            if not fallback_encoding or (primary_encoding and primary_encoding.lower() == fallback_encoding.lower()):
                raise
            logger.warning(
                f"[DB ENCODING] UnicodeDecodeError ao ler dados; tentando fallback '{fallback_encoding}'. Erro: {exc}"
            )
            return _run_with_encoding(fallback_encoding)

    # ---------- Clientes (helpers) ----------
    _CLIENTE_UPDATE_FIELDS = (
        "tipo_pessoa",
        "nome_completo",
        "cpf_cnpj",
        "rg_ie",
        "nacionalidade",
        "estado_civil",
        "profissao",
        "endereco_completo",
        "telefone",
        "email",
        "responsavel_pj",
        "observacoes",
    )

    def _cliente_update_values(self, dados: Dict[str, Any]) -> List[Any]:
        return [dados.get(field) for field in self._CLIENTE_UPDATE_FIELDS]

    def _cliente_insert_values(self, dados: Dict[str, Any], data_cadastro: str) -> Params:
        values = self._cliente_update_values(dados)
        values.insert(-1, data_cadastro)
        return cast(Params, tuple(values))

    # ---------- Process Participants ----------
    def get_process_participants(self, process_id: str):
        return self._execute_query(
            """
            SELECT
                pp.id,
                pp.process_id,
                pp.party_kind,
                pp.party_id,
                pp.role,
                pp.is_primary,

                CASE
                    WHEN pp.party_kind = 'cliente' THEN c.nome_completo
                    WHEN pp.party_kind = 'adverso' THEN pa.nome_completo
                END AS nome,

                CASE
                    WHEN pp.party_kind = 'cliente' THEN c.cpf_cnpj
                    WHEN pp.party_kind = 'adverso' THEN pa.cpf_cnpj
                END AS cpf_cnpj,

                CASE
                    WHEN pp.party_kind = 'cliente' THEN c.endereco_completo
                    WHEN pp.party_kind = 'adverso' THEN pa.endereco_completo
                END AS endereco

            FROM process_participants pp
            LEFT JOIN clientes c
                ON pp.party_kind = 'cliente'
            AND c.id_cliente::text = pp.party_id
            AND c.tenant_id = pp.tenant_id
            LEFT JOIN partes_adversas pa
                ON pp.party_kind = 'adverso'
            AND pa.id::text = pp.party_id
            AND pa.tenant_id = pp.tenant_id
            WHERE pp.tenant_id = %s
            AND pp.process_id = %s
            ORDER BY
                pp.is_primary DESC,
                pp.role,
                pp.id
            """,
            (self.tenant_id, process_id),
            fetch="all",
        )



    def list_process_participants(self, process_id: str):
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, party_kind, party_id, role, is_primary, created_at, updated_at
            FROM process_participants
            WHERE tenant_id = %s AND process_id = %s
            ORDER BY role ASC, is_primary DESC, id ASC
            """,
            (str(self.tenant_id), str(process_id)),
            fetch="all",
        ) or []


    def seed_process_participants(self) -> dict:
        """
        Backfill: cria vínculos em process_participants para processos existentes.
        - vincula o cliente do processo como (role=tipo_parte ou autor) e primary=true
        - vincula todas as partes adversas como role oposto ao cliente e primary=false
        Não duplica: ON CONFLICT DO NOTHING.
        """
        # 1) Cliente do processo -> participante PRIMARY
        q1 = """
        INSERT INTO process_participants (tenant_id, process_id, party_kind, party_id, role, is_primary)
        SELECT
        p.tenant_id,
        p.id_processo::text,
        'cliente'::text,
        p.id_cliente::text,
        COALESCE(NULLIF(LOWER(p.tipo_parte), ''), 'autor')::text,
        TRUE
        FROM processos p
        WHERE p.tenant_id = %s
        AND p.id_cliente IS NOT NULL
        ON CONFLICT (tenant_id, process_id, party_kind, party_id, role) DO NOTHING;
        """
        self._execute_query(q1, (self.tenant_id,), fetch=None)

        # 2) Partes adversas -> papel oposto (DEFAULT reu), primary=false
        # Se tipo_parte do processo for 'reu', o oposto vira 'autor'. Caso contrário, 'reu'.
        q2 = """
        INSERT INTO process_participants (tenant_id, process_id, party_kind, party_id, role, is_primary)
        SELECT
        pa.tenant_id,
        pa.id_processo::text,
        'adverso'::text,
        pa.id::text,
        CASE
            WHEN LOWER(COALESCE(p.tipo_parte, 'autor')) = 'reu' THEN 'autor'
            ELSE 'reu'
        END::text,
        FALSE
        FROM partes_adversas pa
        JOIN processos p
        ON p.tenant_id = pa.tenant_id
        AND p.id_processo = pa.id_processo
        WHERE pa.tenant_id = %s
        ON CONFLICT (tenant_id, process_id, party_kind, party_id, role) DO NOTHING;
        """
        self._execute_query(q2, (self.tenant_id,), fetch=None)

        # 3) Garante que exista 1 primary no polo oposto (autor/reu), se já houver adversos
        # Se já existe primary para esse role, não mexe.
        q3 = """
        WITH role_oposto AS (
        SELECT
            p.tenant_id,
            p.id_processo::text AS process_id,
            CASE
            WHEN LOWER(COALESCE(p.tipo_parte, 'autor')) = 'reu' THEN 'autor'
            ELSE 'reu'
            END AS opposite_role
        FROM processos p
        WHERE p.tenant_id = %s
        ),
        has_primary AS (
        SELECT tenant_id, process_id, role
        FROM process_participants
        WHERE tenant_id = %s AND is_primary = TRUE
        GROUP BY tenant_id, process_id, role
        ),
        candidate AS (
        SELECT pp.id
        FROM process_participants pp
        JOIN role_oposto ro
            ON ro.tenant_id = pp.tenant_id
        AND ro.process_id = pp.process_id
        AND ro.opposite_role = pp.role
        LEFT JOIN has_primary hp
            ON hp.tenant_id = pp.tenant_id
        AND hp.process_id = pp.process_id
        AND hp.role = pp.role
        WHERE pp.tenant_id = %s
            AND pp.party_kind = 'adverso'
            AND pp.is_primary = FALSE
            AND hp.tenant_id IS NULL
        ORDER BY pp.process_id, pp.id
        )
        UPDATE process_participants
        SET is_primary = TRUE
        WHERE id IN (SELECT id FROM candidate);
        """
        self._execute_query(q3, (self.tenant_id, self.tenant_id, self.tenant_id), fetch=None)

        return {"ok": True}



    def upsert_process_participant(
        self,
        *,
        process_id: str,
        party_kind: str,
        party_id: str,
        role: str,
        is_primary: bool = False,
    ) -> int:
        # Se is_primary=True, primeiro derruba primário anterior para o mesmo role
        if is_primary:
            self._execute_query(
                """
                UPDATE process_participants
                SET is_primary = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE tenant_id = %s AND process_id = %s AND role = %s AND is_primary = TRUE
                """,
                (self.tenant_id, str(process_id), str(role)),
                fetch=None,
            )

        row = self._execute_query(
            """
            INSERT INTO process_participants (tenant_id, process_id, party_kind, party_id, role, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, process_id, party_kind, party_id, role)
            DO UPDATE SET
            is_primary = EXCLUDED.is_primary,
            updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                self.tenant_id,
                str(process_id),
                str(party_kind),
                str(party_id),
                str(role),
                bool(is_primary),
            ),
            fetch="one",
        )

        return int(row["id"])

    def delete_process_participant(self, participant_id: int) -> None:
        self._execute_query(
            """
            DELETE FROM process_participants
            WHERE tenant_id = %s AND id = %s
            """,
            (self.tenant_id, int(participant_id)),
            fetch=None,
        )

    def get_primary_participant(self, process_id: str, role: str) -> Optional[Dict[str, Any]]:
        return self._execute_query(
            """
            SELECT id, tenant_id, process_id, party_kind, party_id, role, is_primary
            FROM process_participants
            WHERE tenant_id = %s AND process_id = %s AND role = %s AND is_primary = TRUE
            LIMIT 1
            """,
            (self.tenant_id, str(process_id), str(role)),
            fetch="one",
        )


    def save_cliente(
        self,
        dados: Dict[str, Any],
        id_cliente: Optional[str] = None,
    ) -> Optional[str]:

        try:
            if id_cliente:
                # UPDATE
                cliente_atual = self.get_cliente_by_id(id_cliente)
                if not cliente_atual:
                    raise ValueError(f"Cliente com ID {id_cliente} não encontrado.")

                dados_completos = {**cliente_atual, **dados}

                if self.multi_tenant:
                    query = """
                        UPDATE clientes SET 
                            tipo_pessoa=%s, nome_completo=%s, cpf_cnpj=%s, rg_ie=%s,
                            nacionalidade=%s, estado_civil=%s, profissao=%s, 
                            endereco_completo=%s, telefone=%s, email=%s, 
                            responsavel_pj=%s, observacoes=%s
                        WHERE id_cliente=%s AND tenant_id=%s
                    """
                    update_values = self._cliente_update_values(dados_completos)
                    params = cast(Params, tuple(update_values + [id_cliente, self.tenant_id]))
                else:
                    query = """
                        UPDATE clientes SET 
                            tipo_pessoa=%s, nome_completo=%s, cpf_cnpj=%s, rg_ie=%s,
                            nacionalidade=%s, estado_civil=%s, profissao=%s, 
                            endereco_completo=%s, telefone=%s, email=%s, 
                            responsavel_pj=%s, observacoes=%s
                        WHERE id_cliente=%s
                    """
                    update_values = self._cliente_update_values(dados_completos)
                    params = cast(Params, tuple(update_values + [id_cliente]))

                self._execute_query(query, params)

            else:
                # INSERT - permanece como já estava
                if self.multi_tenant:
                    query = """
                        INSERT INTO clientes (
                            tipo_pessoa, nome_completo, cpf_cnpj, rg_ie, nacionalidade, 
                            estado_civil, profissao, endereco_completo, telefone, email, 
                            responsavel_pj, data_cadastro, observacoes, tenant_id
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id_cliente
                    """
                    insert_values = list(self._cliente_insert_values(dados, datetime.now().strftime("%Y-%m-%d")))
                    insert_values.append(self.tenant_id)
                    params = cast(Params, tuple(insert_values))
                else:
                    query = """
                        INSERT INTO clientes (
                            tipo_pessoa, nome_completo, cpf_cnpj, rg_ie, nacionalidade, 
                            estado_civil, profissao, endereco_completo, telefone, email, 
                            responsavel_pj, data_cadastro, observacoes
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id_cliente
                    """
                    params = self._cliente_insert_values(dados, datetime.now().strftime("%Y-%m-%d"))

                result = self._execute_query(query, params, fetch="one")
                id_cliente = str(result['id_cliente']) if result else None

            return id_cliente
        except Exception as e:
            logger.error(f"Erro ao salvar cliente: {e}", exc_info=True)
            return None

        
            

    def delete_cliente(self, id_cliente: str) -> bool:
        where_sql, params = self._with_tenant_where(
            "WHERE id_cliente = %s",
            cast(Params, (id_cliente,)),
        )
        rowcount = self._execute_query(f"DELETE FROM clientes {where_sql}", params)
        return rowcount > 0

    def get_processos_do_cliente(self, id_cliente: str) -> List[Dict[str, Any]]:
        where_sql, params = self._with_tenant_where(
            "WHERE id_cliente = %s",
            cast(Params, (id_cliente,)),
        )
        query = f"SELECT * FROM processos {where_sql} ORDER BY data_inicio DESC"
        return self._execute_query(query, params, fetch="all")

    def get_processo_by_id(self, id_processo: str):
        """
        Busca o processo usando a coluna correta identificada no pgAdmin.
        O valor 'caso_8d9e73b3' está na coluna 'id_processo'.
        Adicionado log para depuração do filtro de tenant.
        """
        where_sql, params = self._with_tenant_where(
            "WHERE id_processo = %s",
            cast(Params, (id_processo,)),
        )
        query = f"SELECT * FROM processos {where_sql}"
        logger.warning(f"[DEBUG get_processo_by_id] Query: {query} | Params: {params} | multi_tenant={self.multi_tenant}")
        return self._execute_query(query, params, fetch="one")
        
    def save_processo(self, dados: Dict[str, Any], id_processo: Optional[str] = None) -> str:
        """
        Salva ou atualiza um processo com suporte aos 12 novos campos (Item 1).

        Novos campos (Migration 0005):
        - local_tramite, comarca, area_atuacao, instancia, subfase, assunto
        - valor_causa, data_distribuicao, data_encerramento, sentenca
        - em_execucao, segredo_justica

        Validações aplicadas:
        - area_atuacao: enum (Civil, Trabalhista, Penal, Tributario, Familia)
        - instancia: enum (1ª Instância, 2ª Instância, Superior)
        - subfase: enum (Inicial, Instrução, Sentenciado, Recursal, Execução)
        - valor_causa: decimal positivo
        - data_distribuicao/data_encerramento: não podem ser futuras
        """
        if not dados.get("id_cliente") or not dados.get("nome_caso"):
            raise ValueError("ID do Cliente e Nome do Caso são obrigatórios.")

        # Normalize tipo_parte to lowercase
        tipo_parte = dados.get("tipo_parte")
        if tipo_parte:
            tipo_parte = tipo_parte.lower()

        # === VALIDAÇÕES DOS NOVOS CAMPOS (Item 1) ===

        # 1. Validar area_atuacao
        area_atuacao = dados.get("area_atuacao")
        if area_atuacao:
            valid_areas = ["Civil", "Trabalhista", "Penal", "Tributario", "Familia"]
            if area_atuacao not in valid_areas:
                raise ValueError(f"area_atuacao inválida. Valores válidos: {', '.join(valid_areas)}")

        # 2. Validar instancia (aceita forma numérica e extensa)
        instancia = dados.get("instancia")
        if instancia:
            # Mapeamento de valores aceitos
            instancia_map = {
                "1ª Instância": "1ª Instância",
                "1a Instancia": "1ª Instância",
                "Primeira Instância": "1ª Instância",
                "Primeira Instancia": "1ª Instância",
                "2ª Instância": "2ª Instância",
                "2a Instancia": "2ª Instância",
                "Segunda Instância": "2ª Instância",
                "Segunda Instancia": "2ª Instância",
                "Superior": "Superior",
                "Tribunal": "Superior",
                "Tribunais Superiores": "Superior",
            }

            # Normalizar valor
            instancia_normalizada = instancia_map.get(instancia, instancia)

            valid_instancias = ["1ª Instância", "2ª Instância", "Superior"]
            if instancia_normalizada not in valid_instancias:
                raise ValueError(f"instancia inválida '{instancia}'. Valores válidos: {', '.join(valid_instancias)}")

            # Atualizar com valor normalizado
            dados["instancia"] = instancia_normalizada

        # 3. Validar subfase
        subfase = dados.get("subfase")
        if subfase:
            valid_subfases = ["Inicial", "Instrução", "Sentenciado", "Recursal", "Execução"]
            if subfase not in valid_subfases:
                raise ValueError(f"subfase inválida. Valores válidos: {', '.join(valid_subfases)}")

        # 4. Validar valor_causa (decimal positivo)
        valor_causa = dados.get("valor_causa")
        if valor_causa is not None:
            try:
                from decimal import Decimal

                valor_causa = Decimal(str(valor_causa))
                if valor_causa < 0:
                    raise ValueError("valor_causa deve ser positivo")
            except Exception as e:
                raise ValueError(f"valor_causa inválido: {e}")

        # 5. Validar datas (não podem ser futuras)
        hoje = datetime.now().date()

        data_distribuicao = dados.get("data_distribuicao")
        if data_distribuicao:
            if isinstance(data_distribuicao, str):
                data_distribuicao = datetime.strptime(data_distribuicao, "%Y-%m-%d").date()
            if data_distribuicao > hoje:
                logger.warning(f"data_distribuicao está no futuro: {data_distribuicao}")

        data_encerramento = dados.get("data_encerramento")
        if data_encerramento:
            if isinstance(data_encerramento, str):
                data_encerramento = datetime.strptime(data_encerramento, "%Y-%m-%d").date()
            if data_encerramento > hoje:
                logger.warning(f"data_encerramento está no futuro: {data_encerramento}")

        # 6. Normalizar booleanos
        em_execucao = dados.get("em_execucao")
        if em_execucao is not None:
            em_execucao = bool(em_execucao)

        segredo_justica = dados.get("segredo_justica")
        if segredo_justica is not None:
            segredo_justica = bool(segredo_justica)

        # === CONSTRUÇÃO DA QUERY COM 12 NOVOS CAMPOS ===

        if id_processo:
            # UPDATE - atualiza processo existente

            # === VALIDAÇÃO Item 2: Impedir alteração do numero_cnj ===
            if dados.get("numero_cnj"):
                # Buscar numero_cnj atual do processo
                check_query = "SELECT numero_cnj FROM processos WHERE id_processo=%s"
                check_params: Params = (id_processo,)
                if self.multi_tenant:
                    check_query += " AND tenant_id=%s"
                    check_params = (id_processo, self.tenant_id)

                resultado = self._execute_query(check_query, check_params, fetch="all")

                if resultado:
                    numero_cnj_atual = resultado[0].get("numero_cnj")
                    numero_cnj_novo = dados.get("numero_cnj")

                    # Se numero_cnj está sendo alterado, bloquear
                    if numero_cnj_atual and numero_cnj_novo and numero_cnj_atual != numero_cnj_novo:
                        raise ValueError(
                            f"O número CNJ não pode ser alterado após a criação do processo. "
                            f"Valor atual: {numero_cnj_atual}. "
                            f"Se o número está incorreto, delete o processo e recrie-o."
                        )

            if self.multi_tenant:
                query = """UPDATE processos SET 
                    nome_caso=%s, numero_cnj=%s, status=%s, advogado_oab=%s, tipo_parte=%s,
                    local_tramite=%s, comarca=%s, area_atuacao=%s, instancia=%s, subfase=%s, assunto=%s,
                    valor_causa=%s, data_distribuicao=%s, data_encerramento=%s, sentenca=%s,
                    em_execucao=%s, segredo_justica=%s
                    WHERE id_processo=%s AND tenant_id=%s"""
                params = cast(
                    Params,
                    (
                        dados.get("nome_caso"),
                        dados.get("numero_cnj"),
                        dados.get("status"),
                        dados.get("advogado_oab"),
                        tipo_parte,
                        dados.get("local_tramite"),
                        dados.get("comarca"),
                        area_atuacao,
                        instancia,
                        subfase,
                        dados.get("assunto"),
                        valor_causa,
                        data_distribuicao,
                        data_encerramento,
                        dados.get("sentenca"),
                        em_execucao,
                        segredo_justica,
                        id_processo,
                        self.tenant_id,
                    ),
                )
            else:
                query = """UPDATE processos SET 
                    nome_caso=%s, numero_cnj=%s, status=%s, advogado_oab=%s, tipo_parte=%s,
                    local_tramite=%s, comarca=%s, area_atuacao=%s, instancia=%s, subfase=%s, assunto=%s,
                    valor_causa=%s, data_distribuicao=%s, data_encerramento=%s, sentenca=%s,
                    em_execucao=%s, segredo_justica=%s
                    WHERE id_processo=%s"""
                params = cast(
                    Params,
                    (
                        dados.get("nome_caso"),
                        dados.get("numero_cnj"),
                        dados.get("status"),
                        dados.get("advogado_oab"),
                        tipo_parte,
                        dados.get("local_tramite"),
                        dados.get("comarca"),
                        area_atuacao,
                        instancia,
                        subfase,
                        dados.get("assunto"),
                        valor_causa,
                        data_distribuicao,
                        data_encerramento,
                        dados.get("sentenca"),
                        em_execucao,
                        segredo_justica,
                        id_processo,
                    ),
                )
        else:
            # INSERT - cria novo processo (construção dinâmica apenas com campos fornecidos)
            id_processo = f"caso_{str(uuid.uuid4())[:8]}"

            # Campos obrigatórios
            campos = ["id_processo", "id_cliente", "nome_caso", "status", "data_inicio"]
            valores = [
                id_processo,
                dados.get("id_cliente"),
                dados.get("nome_caso"),
                dados.get("status", "PENDENTE"),
                datetime.now().strftime("%Y-%m-%d"),
            ]

            # Adicionar campos opcionais apenas se presentes
            campos_opcionais = {
                "numero_cnj": dados.get("numero_cnj"),
                "tipo_parte": tipo_parte,
                "local_tramite": dados.get("local_tramite"),
                "comarca": dados.get("comarca"),
                "area_atuacao": area_atuacao,
                "instancia": instancia,
                "subfase": subfase,
                "assunto": dados.get("assunto"),
                "valor_causa": valor_causa,
                "data_distribuicao": data_distribuicao,
                "data_encerramento": data_encerramento,
                "sentenca": dados.get("sentenca"),
                "em_execucao": em_execucao,
                "segredo_justica": segredo_justica,
            }

            # Adicionar advogado_oab apenas se existir na tabela advogados
            advogado_oab = dados.get("advogado_oab")
            if advogado_oab:
                # Verificar se advogado existe
                try:
                    if self.multi_tenant:
                        check_query = "SELECT 1 FROM advogados WHERE oab = %s AND tenant_id = %s"
                        result = self._execute_query(
                            check_query,
                            (advogado_oab, self.tenant_id),
                            fetch="one",
                        )
                    else:
                        check_query = "SELECT 1 FROM advogados WHERE oab = %s"
                        result = self._execute_query(
                            check_query,
                            (advogado_oab,),
                            fetch="one",
                        )

                    if result:
                        campos_opcionais["advogado_oab"] = advogado_oab
                    else:
                        logger.warning(
                            f"Advogado OAB {advogado_oab} não encontrado, processo será criado sem advogado"
                        )
                except Exception as e:
                    logger.warning(f"Erro ao verificar advogado {advogado_oab}: {e}")

            for campo, valor in campos_opcionais.items():
                if valor is not None:
                    campos.append(campo)
                    valores.append(valor)

            # Adicionar tenant_id se multi-tenant
            if self.multi_tenant:
                campos.append("tenant_id")
                valores.append(self.tenant_id)

            # Construir query dinamicamente
            placeholders = ",".join(["%s"] * len(valores))
            campos_str = ",".join(campos)
            query = f"INSERT INTO processos ({campos_str}) VALUES ({placeholders})"
            params = cast(Params, tuple(valores))

        self._execute_query(query, params)
        logger.info(f"Processo {'atualizado' if id_processo else 'criado'}: {id_processo}")
        return id_processo

    def delete_processo(self, id_processo: str) -> bool:
        where_sql, params = self._with_tenant_where(
            "WHERE id_processo = %s",
            cast(Params, (id_processo,)),
        )
        rowcount = self._execute_query(f"DELETE FROM processos {where_sql}", params)
        return rowcount > 0

    # --- CRUD Partes Adversas (Item 3 - Migration 0006) ---

    def _validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """
        Valida CPF (11 dígitos) ou CNPJ (14 dígitos).
        Retorna True se válido, False caso contrário.
        """
        import re

        if not cpf_cnpj:
            return True  # Opcional, permite vazio

        # Remove caracteres não-numéricos
        numeros = re.sub(r"\D", "", cpf_cnpj)

        # Valida CPF (11 dígitos)
        if len(numeros) == 11:
            # CPF inválidos conhecidos (todos dígitos iguais)
            if numeros == numeros[0] * 11:
                return False

            # Validação simplificada (algoritmo completo seria muito extenso)
            # Aceita qualquer CPF com 11 dígitos numéricos distintos
            return True

        # Valida CNPJ (14 dígitos)
        if len(numeros) == 14:
            # CNPJ inválidos conhecidos
            if numeros == numeros[0] * 14:
                return False

            # Validação simplificada
            return True

        return False  # Tamanho inválido

    def _buscar_cep_viacep(self, cep: str) -> Optional[Dict[str, str]]:
        """
        Busca informações de endereço via API ViaCEP.
        Retorna dict com {logradouro, bairro, cidade, estado} ou None se falhar.
        """
        import re
        import requests

        if not cep:
            return None

        # Remove caracteres não-numéricos
        cep_limpo = re.sub(r"\D", "", cep)

        if len(cep_limpo) != 8:
            logger.warning(f"CEP inválido (deve ter 8 dígitos): {cep}")
            return None

        try:
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            dados = response.json()

            # ViaCEP retorna {"erro": true} se CEP não existe
            if dados.get("erro"):
                logger.warning(f"CEP não encontrado: {cep_limpo}")
                return None

            return {
                "logradouro": dados.get("logradouro", ""),
                "bairro": dados.get("bairro", ""),
                "cidade": dados.get("localidade", ""),
                "estado": dados.get("uf", ""),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao consultar ViaCEP para CEP {cep_limpo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar CEP {cep_limpo}: {e}")
            return None

    def save_documento(self, dados: Dict[str, Any]) -> int:
        logger.info(f"[DOCUMENTOS] Tentando salvar documento: {dados}")
        """
        Insere um documento na tabela documentos.
        Retorna o ID criado.
        """
        query = """
            INSERT INTO documentos (
                id_cliente, id_processo, tipo, titulo, descricao,
                arquivo_nome, mime_type, tamanho_bytes,
                storage_backend, storage_path,
                checksum_sha256, criado_por_id, tenant_id,
                created_at, updated_at
            )
            VALUES (
                %s,%s,%s,%s,%s,
                %s,%s,%s,
                %s,%s,
                %s,%s,%s,
                NOW(), NOW()
            )
            RETURNING id
        """

        params = (
            dados.get("id_cliente"),
            dados.get("id_processo"),
            dados.get("tipo"),
            dados.get("titulo"),
            dados.get("descricao"),
            dados.get("arquivo_nome"),
            dados.get("mime_type"),
            dados.get("tamanho_bytes"),
            dados.get("storage_backend"),
            dados.get("storage_path"),
            dados.get("checksum_sha256"),
            dados.get("criado_por_id"),
            self.tenant_id,
        )

        result = self._execute_query(query, params, fetch="one")
        return result["id"]

    def _documento_where(self, base_where: str, params: Params) -> Tuple[str, Params]:
        if self.multi_tenant:
            trimmed = (base_where or "").strip()
            if not trimmed:
                return "WHERE tenant_id = %s", cast(Params, (*params, self.tenant_id))
            if trimmed.lower().startswith("where"):
                return f"{trimmed} AND tenant_id = %s", cast(Params, (*params, self.tenant_id))
            return f"WHERE {trimmed} AND tenant_id = %s", cast(Params, (*params, self.tenant_id))
        return base_where, params

    def _with_tenant_where(self, base_where: str, params: Params) -> Tuple[str, Params]:
        if self.multi_tenant:
            trimmed = (base_where or "").strip()
            if not trimmed:
                return "WHERE tenant_id = %s", cast(Params, (*params, self.tenant_id))
            if trimmed.lower().startswith("where"):
                return f"{trimmed} AND tenant_id = %s", cast(Params, (*params, self.tenant_id))
            return f"WHERE {trimmed} AND tenant_id = %s", cast(Params, (*params, self.tenant_id))
        return base_where, params

    def get_documentos_by_processo(self, id_processo: str) -> List[Dict[str, Any]]:
        where_sql, params = self._documento_where(
            "WHERE id_processo = %s",
            cast(Params, (id_processo,)),
        )
        query = f"""
            SELECT *
            FROM documentos
            {where_sql}
            ORDER BY created_at DESC
        """
        return self._execute_query(query, params, fetch="all") or []

    def get_documento_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        where_sql, params = self._documento_where(
            "WHERE id=%s",
            cast(Params, (doc_id,)),
        )
        query = f"SELECT * FROM documentos {where_sql}"
        return self._execute_query(query, params, fetch="one")


    def update_documento(self, doc_id: int, dados: Dict[str, Any]) -> bool:
        campos = []
        valores = []

        for campo in [
            "tipo",
            "titulo",
            "descricao",
            "mime_type",
            "tamanho_bytes",
            "storage_backend",
            "storage_path",
            "checksum_sha256",
            "criado_por_id",
        ]:
            if dados.get(campo) is not None:
                campos.append(f"{campo}=%s")
                valores.append(dados[campo])

        set_str = ", ".join(campos)

        where_sql, params = self._documento_where(
            "WHERE id=%s",
            cast(Params, (doc_id,)),
        )
        query = f"""
            UPDATE documentos
            SET {set_str}, updated_at=NOW()
            {where_sql}
        """
        valores.extend(params)

        rc = self._execute_query(query, tuple(valores))
        return rc > 0


    def delete_documento(self, doc_id: int) -> bool:
        where_sql, params = self._documento_where(
            "WHERE id=%s",
            cast(Params, (doc_id,)),
        )
        query = f"DELETE FROM documentos {where_sql}"
        rc = self._execute_query(query, params)
        return rc > 0

    def delete_documento_por_titulo(self, id_processo: str, titulo: str) -> bool:
        sql = """
            DELETE FROM documentos
            WHERE tenant_id = %s
            AND id_processo = %s
            AND titulo = %s
        """
        apagados = self._execute_query(sql, (self.tenant_id, id_processo, titulo))
        return apagados > 0

    def delete_documento_by_filename(self, id_processo: str, titulo: str) -> bool:
        """
        Deleta um registro da tabela documentos para este tenant, processo e título.
        Retorna True se ao menos 1 linha foi removida.
        """
        sql = """
            DELETE FROM documentos
            WHERE tenant_id  = %s
            AND id_processo = %s
            AND titulo      = %s
        """
        params = (self.tenant_id, id_processo, titulo)

        apagados = self._execute_query(sql, params)
        return apagados > 0



    def get_partes_adversas_by_processo(self, id_processo: str) -> List[Dict[str, Any]]:
        """
        Retorna todas as partes adversas de um processo.
        Sempre filtra por tenant_id (coluna obrigatória).
        """
        return self._execute_query(
            "SELECT * FROM partes_adversas WHERE id_processo = %s AND tenant_id = %s ORDER BY created_at DESC",
            (id_processo, self.tenant_id),
            fetch="all",
        ) or []

    def get_parte_adversa_by_id(self, id_parte: int) -> Optional[Dict[str, Any]]:
        """
        Retorna uma parte adversa específica por ID.
        Sempre filtra por tenant_id (coluna obrigatória).
        """
        return self._execute_query(
            "SELECT * FROM partes_adversas WHERE id = %s AND tenant_id = %s",
            (id_parte, self.tenant_id),
            fetch="one",
        )

    def save_parte_adversa(self, dados: Dict[str, Any], id_parte: Optional[int] = None) -> int:
        """
        Cria ou atualiza uma parte adversa.

        Campos obrigatórios:
        - id_processo: ID do processo (FK)
        - tipo_parte: enum (autor, reu, terceiro, reclamante, reclamada)
        - nome_completo: nome da pessoa/empresa

        Campos opcionais:
        - cpf_cnpj, rg, qualificacao, endereco_completo, bairro, cidade, estado, cep
        - telefone, email, advogado_nome, advogado_oab, observacoes

        Validações:
        - CPF/CNPJ formato válido (11 ou 14 dígitos)
        - tipo_parte deve ser um dos valores permitidos
        - Se CEP fornecido, tenta buscar endereço via ViaCEP

        Retorna:
        - ID da parte adversa (int)
        """
        # Validações obrigatórias
        if not dados.get("id_processo"):
            raise ValueError("id_processo é obrigatório")

        if not dados.get("nome_completo"):
            raise ValueError("nome_completo é obrigatório")

        # Validar tipo_parte
        tipo_parte = dados.get("tipo_parte", "").lower()
        tipos_validos = ["autor", "reu", "terceiro", "reclamante", "reclamada"]
        if tipo_parte and tipo_parte not in tipos_validos:
            raise ValueError(f"tipo_parte inválido. Valores válidos: {', '.join(tipos_validos)}")

        # Validar CPF/CNPJ se fornecido
        cpf_cnpj = dados.get("cpf_cnpj")
        if cpf_cnpj and not self._validar_cpf_cnpj(cpf_cnpj):
            raise ValueError("CPF/CNPJ inválido. Deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)")

        # Buscar endereço via ViaCEP se CEP fornecido e campos não preenchidos
        cep = dados.get("cep")
        if cep and not dados.get("cidade"):
            endereco_viacep = self._buscar_cep_viacep(cep)
            if endereco_viacep:
                # Preenche apenas campos vazios
                if not dados.get("bairro"):
                    dados["bairro"] = endereco_viacep.get("bairro", "")
                if not dados.get("cidade"):
                    dados["cidade"] = endereco_viacep.get("cidade", "")
                if not dados.get("estado"):
                    dados["estado"] = endereco_viacep.get("estado", "")
                logger.info(
                    "Endereço preenchido via ViaCEP para CEP "
                    f"{cep}: {endereco_viacep.get('cidade')}/{endereco_viacep.get('estado')}"
                )

        # Normalizar campos
        nome_completo = dados.get("nome_completo", "").strip()
        qualificacao = dados.get("qualificacao", "").strip() or None
        endereco_completo = dados.get("endereco_completo", "").strip() or None
        bairro = dados.get("bairro", "").strip() or None
        cidade = dados.get("cidade", "").strip() or None
        estado = dados.get("estado", "").strip() or None
        telefone = dados.get("telefone", "").strip() or None
        email = dados.get("email", "").strip() or None
        advogado_nome = dados.get("advogado_nome", "").strip() or None
        advogado_oab = dados.get("advogado_oab", "").strip() or None
        observacoes = dados.get("observacoes", "").strip() or None

        if id_parte:
            # UPDATE - atualiza parte adversa existente
            if self.multi_tenant:
                query = """UPDATE partes_adversas SET 
                    tipo_parte=%s, nome_completo=%s, cpf_cnpj=%s, rg=%s, qualificacao=%s,
                    endereco_completo=%s, bairro=%s, cidade=%s, estado=%s, cep=%s,
                    telefone=%s, email=%s, advogado_nome=%s, advogado_oab=%s, observacoes=%s,
                    updated_at=NOW()
                    WHERE id=%s AND tenant_id=%s"""
                params = cast(
                    Params,
                    (
                        tipo_parte,
                        nome_completo,
                        cpf_cnpj,
                        dados.get("rg"),
                        qualificacao,
                        endereco_completo,
                        bairro,
                        cidade,
                        estado,
                        cep,
                        telefone,
                        email,
                        advogado_nome,
                        advogado_oab,
                        observacoes,
                        id_parte,
                        self.tenant_id,
                    ),
                )
            else:
                query = """UPDATE partes_adversas SET 
                    tipo_parte=%s, nome_completo=%s, cpf_cnpj=%s, rg=%s, qualificacao=%s,
                    endereco_completo=%s, bairro=%s, cidade=%s, estado=%s, cep=%s,
                    telefone=%s, email=%s, advogado_nome=%s, advogado_oab=%s, observacoes=%s,
                    updated_at=NOW()
                    WHERE id=%s"""
                params = cast(
                    Params,
                    (
                        tipo_parte,
                        nome_completo,
                        cpf_cnpj,
                        dados.get("rg"),
                        qualificacao,
                        endereco_completo,
                        bairro,
                        cidade,
                        estado,
                        cep,
                        telefone,
                        email,
                        advogado_nome,
                        advogado_oab,
                        observacoes,
                        id_parte,
                    ),
                )

            self._execute_query(query, params)
            logger.info(f"Parte adversa atualizada: ID {id_parte}")
            return id_parte

        # INSERT - cria nova parte adversa
        # SEMPRE incluir tenant_id (obrigatório na tabela)
        tenant_id_final = dados.get("tenant_id") or self.tenant_id

        query = """INSERT INTO partes_adversas (
            id_processo, tenant_id, tipo_parte, nome_completo, cpf_cnpj, rg, qualificacao,
            endereco_completo, bairro, cidade, estado, cep,
            telefone, email, advogado_nome, advogado_oab, observacoes,
            created_at, updated_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW()) RETURNING id"""
        params = cast(
            Params,
            (
                dados.get("id_processo"),
                tenant_id_final,
                tipo_parte,
                nome_completo,
                cpf_cnpj,
                dados.get("rg"),
                qualificacao,
                endereco_completo,
                bairro,
                cidade,
                estado,
                cep,
                telefone,
                email,
                advogado_nome,
                advogado_oab,
                observacoes,
            ),
        )

        result = self._execute_query(query, params, fetch="one")
        novo_id = result["id"] if result else None

        if not novo_id:
            raise RuntimeError("Falha ao criar parte adversa: ID não retornado")

        logger.info(f"Parte adversa criada: ID {novo_id} - {nome_completo}")
        return novo_id

    def delete_parte_adversa(self, id_parte: int) -> bool:
        """
        Exclui uma parte adversa por ID.
        Sempre filtra por tenant_id (coluna obrigatória).

        Retorna:
        - True se excluído com sucesso
        - False se não encontrado
        """
        rowcount = self._execute_query(
            "DELETE FROM partes_adversas WHERE id = %s AND tenant_id = %s",
            (id_parte, self.tenant_id),
        )

        if rowcount > 0:
            logger.info(f"Parte adversa excluída: ID {id_parte}")
            return True
        logger.warning(f"Parte adversa não encontrada para exclusão: ID {id_parte}")
        return False

    # --- Fim CRUD Partes Adversas ---

    # --- CRUD Escritorio ---
    def save_escritorio(self, dados: dict):
        """
        Cria ou atualiza o escritório do tenant atual.
        """
        query_check = "SELECT id FROM escritorio WHERE tenant_id = %s"
        existente = self._execute_query(query_check, (self.tenant_id,), fetch="one")

        campos = [
            "razao_social",
            "nome_fantasia",
            "cnpj",
            "endereco_completo",
            "telefones",
            "email_contato",
            "site",
            "responsaveis",
            "areas_atuacao",
        ]

        # Serializa apenas os campos jsonb
        for campo in ["telefones", "responsaveis", "areas_atuacao"]:
            if campo in dados and not isinstance(dados[campo], str):
                dados[campo] = json.dumps(dados[campo], ensure_ascii=False)

        valores = [dados.get(c) for c in campos]

        if existente:
            set_str = ", ".join([f"{c} = %s" for c in campos])
            query = f"UPDATE escritorio SET {set_str} WHERE tenant_id = %s"
            self._execute_query(query, (*valores, self.tenant_id))
        else:
            query = f"""
                INSERT INTO escritorio (tenant_id, {', '.join(campos)})
                VALUES (%s, {', '.join(['%s'] * len(campos))})
            """
            self._execute_query(query, (self.tenant_id, *valores))
        
    def create_usuario(self, username, email, password, nome_completo, advogado_oab=None):
        password_hash = generate_password_hash(password)
        if self.multi_tenant:
            query = (
                "INSERT INTO usuarios (username, email, password_hash, nome_completo, "
                "data_criacao, advogado_oab, tenant_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            params = cast(
                Params,
                (
                    username,
                    email,
                    password_hash,
                    nome_completo,
                    datetime.now(),
                    advogado_oab,
                    self.tenant_id,
                ),
            )
        else:
            query = (
                "INSERT INTO usuarios (username, email, password_hash, nome_completo, data_criacao, advogado_oab) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            params = cast(
                Params,
                (username, email, password_hash, nome_completo, datetime.now(), advogado_oab),
            )
        try:
            self._execute_query(query, params)
            return True
        except psycopg2.IntegrityError:
            logger.error(f"Erro de integridade: usuário ou email '{username}' já existe.")
            return False

    def get_usuario_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        where_sql, params = self._with_tenant_where(
            "WHERE username = %s",
            cast(Params, (username,)),
        )
        query = f"SELECT * FROM usuarios {where_sql}"
        return self._execute_query(query, params, fetch="one")

    def get_usuario_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        where_sql, params = self._with_tenant_where(
            "WHERE id = %s",
            cast(Params, (user_id,)),
        )
        query = f"SELECT * FROM usuarios {where_sql}"
        return self._execute_query(query, params, fetch="one")

    # --- Chat persistence helpers ---
    def save_chat_turn(self, id_processo: str, role: str, content: str):
        if self.multi_tenant:
            query = "INSERT INTO chat_turns (id_processo, role, content, tenant_id) VALUES (%s,%s,%s,%s)"
            params = cast(Params, (id_processo, role, content, self.tenant_id))
        else:
            query = "INSERT INTO chat_turns (id_processo, role, content) VALUES (%s,%s,%s)"
            params = cast(Params, (id_processo, role, content))
        self._execute_query(query, params)

    def get_chat_history(self, id_processo: str, limit: int = 50) -> List[Dict[str, Any]]:
        where_sql, params = self._with_tenant_where(
            "WHERE id_processo=%s",
            cast(Params, (id_processo,)),
        )
        query = f"SELECT role, content, created_at FROM chat_turns {where_sql} ORDER BY id DESC LIMIT %s"
        params = cast(Params, (*params, limit))
        return (self._execute_query(query, params, fetch="all") or [])[::-1]

    # --- Bulk CSV Upload for Multiple Processes ---
    def bulk_create_processos_from_csv(self, id_cliente: str, csv_content: str) -> Dict[str, Any]:
        """
        Cria múltiplos processos a partir de conteúdo CSV.

        Formato esperado (com cabeçalho):
        nome_caso,numero_cnj,status,advogado_oab,tipo_parte
        "Processo de Cobrança #1",123456789012345678,ATIVO,OAB123,autor
        "Ação Indenizatória",223456789012345679,PENDENTE,OAB456,reu

        tipo_parte pode ser: autor, reu, terceiro, reclamante, reclamada

        Returns:
        {
            "status": "sucesso" ou "erro",
            "processos_criados": int,
            "erros": List[str],
            "ids_criados": List[str]
        }
        """
        import csv
        from io import StringIO

        logger.info(f"Iniciando bulk upload CSV para cliente {id_cliente}")
        created_count = 0
        errors = []
        ids_criados = []

        try:
            reader = csv.DictReader(StringIO(csv_content))

            if not reader.fieldnames:
                return {
                    "status": "erro",
                    "mensagem": "CSV vazio ou formato inválido",
                    "processos_criados": 0,
                    "erros": ["Arquivo CSV sem cabeçalho"],
                    "ids_criados": [],
                }

            # Valida colunas obrigatórias
            required_cols = {"nome_caso"}
            missing_cols = required_cols - set(reader.fieldnames)
            if missing_cols:
                return {
                    "status": "erro",
                    "mensagem": f"Colunas obrigatórias faltando: {missing_cols}",
                    "processos_criados": 0,
                    "erros": [f"Colunas obrigatórias: {missing_cols}"],
                    "ids_criados": [],
                }

            # Processa cada linha
            for row_num, row in enumerate(reader, start=2):  # start=2 para pular cabeçalho
                try:
                    # Extrai e valida dados básicos
                    nome_caso = (row.get("nome_caso") or "").strip()
                    numero_cnj = (row.get("numero_cnj") or "").strip()
                    status = (row.get("status") or "PENDENTE").strip()
                    advogado_oab = (row.get("advogado_oab") or "").strip()
                    tipo_parte = (row.get("tipo_parte") or "").strip()

                    # Novos campos do Item 1 (DIA 1)
                    comarca = (row.get("comarca") or "").strip()
                    vara = (row.get("vara") or "").strip()
                    juiz_nome = (row.get("juiz_nome") or "").strip()
                    data_distribuicao = (row.get("data_distribuicao") or "").strip()
                    data_citacao = (row.get("data_citacao") or "").strip()
                    data_audiencia = (row.get("data_audiencia") or "").strip()
                    valor_causa = (row.get("valor_causa") or "").strip()
                    valor_condenacao = (row.get("valor_condenacao") or "").strip()
                    tipo_acao = (row.get("tipo_acao") or "").strip()
                    grau_jurisdicao = (row.get("grau_jurisdicao") or "").strip()
                    instancia = (row.get("instancia") or "").strip()
                    observacoes = (row.get("observacoes") or "").strip()

                    if not nome_caso:
                        errors.append(f"Linha {row_num}: nome_caso vazio")
                        continue

                    # Valida tipo_parte se fornecido
                    valid_tipos = {"autor", "reu", "terceiro", "reclamante", "reclamada"}
                    if tipo_parte and tipo_parte.lower() not in valid_tipos:
                        errors.append(
                            f"Linha {row_num}: tipo_parte inválido. Valores válidos: {', '.join(valid_tipos)}"
                        )
                        continue

                    # Monta dados do processo (apenas campos com valores)
                    dados_processo = {
                        "id_cliente": id_cliente,
                        "nome_caso": nome_caso,
                        "status": status if status else "PENDENTE",
                    }

                    # Adiciona campos opcionais apenas se tiverem valores
                    if numero_cnj:
                        dados_processo["numero_cnj"] = numero_cnj
                    if advogado_oab:
                        dados_processo["advogado_oab"] = advogado_oab
                    if tipo_parte:
                        dados_processo["tipo_parte"] = tipo_parte.lower()
                    if comarca:
                        dados_processo["comarca"] = comarca
                    if vara:
                        dados_processo["vara"] = vara
                    if juiz_nome:
                        dados_processo["juiz_nome"] = juiz_nome
                    if data_distribuicao:
                        dados_processo["data_distribuicao"] = data_distribuicao
                    if data_citacao:
                        dados_processo["data_citacao"] = data_citacao
                    if data_audiencia:
                        dados_processo["data_audiencia"] = data_audiencia
                    if valor_causa:
                        try:
                            dados_processo["valor_causa"] = float(valor_causa.replace(",", "."))
                        except ValueError:
                            errors.append(f"Linha {row_num}: valor_causa inválido '{valor_causa}'")
                            continue
                    if valor_condenacao:
                        try:
                            dados_processo["valor_condenacao"] = float(valor_condenacao.replace(",", "."))
                        except ValueError:
                            errors.append(
                                f"Linha {row_num}: valor_condenacao inválido '{valor_condenacao}'"
                            )
                            continue
                    if tipo_acao:
                        dados_processo["tipo_acao"] = tipo_acao
                    if grau_jurisdicao:
                        dados_processo["grau_jurisdicao"] = grau_jurisdicao
                    if instancia:
                        dados_processo["instancia"] = instancia
                    if observacoes:
                        dados_processo["observacoes"] = observacoes

                    # Cria processo
                    proc_id = self.save_processo(dados_processo)
                    ids_criados.append(proc_id)
                    created_count += 1
                    logger.info(f"Processo criado: {proc_id} (linha {row_num})")

                except Exception as e:
                    errors.append(f"Linha {row_num}: {str(e)}")
                    logger.warning(f"Erro na linha {row_num}: {e}")

            status_final = "sucesso" if created_count > 0 else "erro"
            if created_count == 0 and not errors:
                errors.append("Nenhuma linha válida no CSV")

            resultado = {
                "status": status_final,
                "processos_criados": created_count,
                "erros": errors,
                "ids_criados": ids_criados,
            }

            logger.info(f"Bulk upload concluído: {created_count} processos criados, {len(errors)} erros")
            return resultado

        except Exception as e:
            logger.error(f"Erro geral ao processar CSV: {e}", exc_info=True)
            return {
                "status": "erro",
                "mensagem": str(e),
                "processos_criados": 0,
                "erros": [str(e)],
                "ids_criados": [],
            }

    def get_advogado_by_oab(self, oab):
        """Busca dados do advogado para a petição."""
        query = "SELECT * FROM advogados WHERE oab = %s AND tenant_id = %s"
        return self._execute_query(query, (oab, self.tenant_id), fetch="one")

    def get_cliente_by_id(self, id_cliente):
        """Busca dados do autor para a qualificação da petição."""
        query = "SELECT * FROM clientes WHERE id_cliente::text = %s AND tenant_id = %s"
        return self._execute_query(query, (str(id_cliente), self.tenant_id), fetch="one")
