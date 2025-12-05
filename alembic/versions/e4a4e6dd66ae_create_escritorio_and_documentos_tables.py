"""create escritorio and documentos tables

Revision ID: e4a4e6dd66ae
Revises: a8e0689d250a
Create Date: 2025-12-05 18:56:51.403324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4a4e6dd66ae'
down_revision: Union[str, None] = 'a8e0689d250a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    op.execute("""
    -- Table: public.escritorio

    -- DROP TABLE IF EXISTS public.escritorio;

    CREATE TABLE IF NOT EXISTS public.escritorio
    (
        id integer NOT NULL,
        razao_social text COLLATE pg_catalog."default",
        nome_fantasia text COLLATE pg_catalog."default",
        cnpj text COLLATE pg_catalog."default",
        endereco_completo text COLLATE pg_catalog."default",
        telefones jsonb,
        email_contato text COLLATE pg_catalog."default",
        site text COLLATE pg_catalog."default",
        responsaveis jsonb,
        areas_atuacao jsonb,
        CONSTRAINT escritorio_pkey PRIMARY KEY (id)
    )

    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.escritorio
        OWNER to postgres;
    """)

    op.execute("""
    -- Table: public.documentos

    -- DROP TABLE IF EXISTS public.documentos;

    CREATE TABLE IF NOT EXISTS public.documentos
    (
        id integer NOT NULL DEFAULT nextval('documentos_id_seq'::regclass),
        tenant_id text COLLATE pg_catalog."default" NOT NULL,
        id_cliente character varying(50) COLLATE pg_catalog."default" NOT NULL,
        id_processo character varying(50) COLLATE pg_catalog."default" NOT NULL,
        tipo character varying(20) COLLATE pg_catalog."default" NOT NULL,
        titulo character varying(255) COLLATE pg_catalog."default" NOT NULL,
        descricao text COLLATE pg_catalog."default",
        arquivo_nome character varying(255) COLLATE pg_catalog."default" NOT NULL,
        mime_type character varying(100) COLLATE pg_catalog."default",
        tamanho_bytes bigint,
        storage_backend character varying(50) COLLATE pg_catalog."default" NOT NULL DEFAULT 'local'::character varying,
        storage_path character varying(500) COLLATE pg_catalog."default" NOT NULL,
        checksum_sha256 character varying(64) COLLATE pg_catalog."default",
        criado_por_id integer NOT NULL,
        created_at timestamp without time zone NOT NULL DEFAULT now(),
        updated_at timestamp without time zone NOT NULL DEFAULT now(),
        CONSTRAINT documentos_pkey PRIMARY KEY (id),
        CONSTRAINT fk_documentos_clientes FOREIGN KEY (id_cliente)
            REFERENCES public.clientes (id_cliente) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION,
        CONSTRAINT fk_documentos_processos FOREIGN KEY (id_processo)
            REFERENCES public.processos (id_processo) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION,
        CONSTRAINT fk_documentos_usuarios FOREIGN KEY (criado_por_id)
            REFERENCES public.usuarios (id) MATCH SIMPLE
            ON UPDATE NO ACTION
            ON DELETE NO ACTION
    )

    TABLESPACE pg_default;

    ALTER TABLE IF EXISTS public.documentos
        OWNER to postgres;
    -- Index: ix_documentos_checksum

    -- DROP INDEX IF EXISTS public.ix_documentos_checksum;

    CREATE INDEX IF NOT EXISTS ix_documentos_checksum
        ON public.documentos USING btree
        (checksum_sha256 COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;
    -- Index: ix_documentos_id_cliente

    -- DROP INDEX IF EXISTS public.ix_documentos_id_cliente;

    CREATE INDEX IF NOT EXISTS ix_documentos_id_cliente
        ON public.documentos USING btree
        (id_cliente COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;
    -- Index: ix_documentos_id_processo

    -- DROP INDEX IF EXISTS public.ix_documentos_id_processo;

    CREATE INDEX IF NOT EXISTS ix_documentos_id_processo
        ON public.documentos USING btree
        (id_processo COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;
    -- Index: ix_documentos_tenant_id

    -- DROP INDEX IF EXISTS public.ix_documentos_tenant_id;

    CREATE INDEX IF NOT EXISTS ix_documentos_tenant_id
        ON public.documentos USING btree
        (tenant_id COLLATE pg_catalog."default" ASC NULLS LAST)
        TABLESPACE pg_default;
        """)
            


def downgrade() -> None:
    # Reverso do upgrade
    op.execute("DROP TABLE IF EXISTS documentos;")
    op.execute("DROP TABLE IF EXISTS escritorio;")
