"""create petition_templates and petition_versions tables

Revision ID: rev_20260102_petition_tpl
Revises: 20260102_alter_petitions_ids
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "rev_20260102_petition_tpl"
down_revision: Union[str, None] = "20260102_alter_petitions_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "petition_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("body_jinja", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_petition_templates_tenant_code"),
    )

    op.create_table(
        "petition_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("petition_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("rendered_content", sa.Text(), nullable=False),
        sa.Column("context_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["petition_id"], ["petitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "petition_id", "version", name="uq_petition_versions_tenant_petition_version"),
    )

    seed_sql = """
INSERT INTO public.petition_templates (tenant_id, code, title, body_jinja, is_active)
VALUES
(
  'public',
  'INICIAL_PADRAO',
  'Pet\u00ed\u00e7\u00e3o Inicial - Padr\u00e3o',
$$EXCELENT\u00cdSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA {{ processo.local_tramite or '___' }} VARA {{ (processo.area_atuacao or 'C\u00edvel') }} DA COMARCA DE {{ processo.comarca or '___' }}.

{{ cliente.nome_completo or 'AUTOR' }}, j\u00e1 qualificado(a) nos autos (ou a qualificar), por seu advogado {{ advogado.nome_completo or 'ADVOGADO' }}, OAB {{ advogado.oab or advogado.advogado_oab or '___' }}, vem, respeitosamente, \u00e0 presen\u00e7a de Vossa Excel\u00eancia, propor a presente

A\u00c7\u00c3O {{ content.tipo_acao or '________________' }}

em face de {{ reu.nome_completo or reu.nome or 'R\u00c9U' }}, pelos fatos e fundamentos a seguir expostos.

I. DOS FATOS
{{ content.fatos or '[Descreva os fatos aqui]' }}

II. DO DIREITO
{{ content.fundamentos or '[Fundamenta\u00e7\u00e3o jur\u00eddica aqui]' }}

III. DOS PEDIDOS
{{ content.pedidos or '[Liste os pedidos aqui]' }}

IV. DAS PROVAS
{{ content.provas or '[Indique as provas aqui]' }}

V. REQUERIMENTOS FINAIS
Requer-se a cita\u00e7\u00e3o da parte r\u00e9 e a proced\u00eancia dos pedidos, com condena\u00e7\u00e3o nas verbas cab\u00edveis.

{{ content.local_data_assinatura or (processo.comarca or 'Cidade') ~ ', ' ~ hoje }}

____________________________________
{{ advogado.nome_completo or 'ADVOGADO' }}
OAB {{ advogado.oab or advogado.advogado_oab or '___' }}
$$,
    true
)
ON CONFLICT (tenant_id, code) DO UPDATE
SET title = EXCLUDED.title,
    body_jinja = EXCLUDED.body_jinja,
    is_active = true,
    updated_at = now();
"""

    op.execute(sa.text(seed_sql))

    contest_seed_sql = """
INSERT INTO public.petition_templates (tenant_id, code, title, body_jinja, is_active)
VALUES
(
  'public',
  'CONTESTACAO_PADRAO',
  'Contesta\u00e7\u00e3o - Padr\u00e3o',
$$EXCELENT\u00cdSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA {{ processo.local_tramite or '___' }} VARA {{ (processo.area_atuacao or 'C\u00edvel') }} DA COMARCA DE {{ processo.comarca or '___' }}.

Processo: {{ processo.numero_cnj or processo.id_processo or '___' }}

{{ reu.nome_completo or reu.nome or 'R\u00c9U' }}, por seu advogado, vem, respeitosamente, apresentar

CONTESTA\u00c7\u00c3O

\u00e0 a\u00e7\u00e3o proposta por {{ cliente.nome_completo or 'AUTOR' }}, pelos fundamentos abaixo.

I. S\u00cdNTESE DA INICIAL
{{ content.fatos or '[S\u00edntese do que foi alegado na inicial / pontos controvertidos]' }}

II. PRELIMINARES (SE HOUVER)
{{ content.fundamentos or '[Preliminares e quest\u00f5es processuais]' }}

III. DO M\u00c9RITO
{{ content.pedidos or '[Argumenta\u00e7\u00e3o de m\u00e9rito e refuta\u00e7\u00e3o dos pedidos]' }}

IV. PROVAS
{{ content.provas or '[Indica\u00e7\u00e3o de provas]' }}

V. PEDIDOS
Diante do exposto, requer-se a improced\u00eancia dos pedidos autorais e o que mais for de direito.

{{ content.local_data_assinatura or (processo.comarca or 'Cidade') ~ ', ' ~ hoje }}

____________________________________
ADVOGADO
OAB ___
$$,
  true
)
ON CONFLICT (tenant_id, code) DO UPDATE
SET title = EXCLUDED.title,
    body_jinja = EXCLUDED.body_jinja,
    is_active = true,
    updated_at = now();
"""

    op.execute(sa.text(contest_seed_sql))

    replica_seed_sql = """
INSERT INTO public.petition_templates (tenant_id, code, title, body_jinja, is_active)
VALUES
(
  'public',
  'REPLICA_PADRAO',
  'R\u00e9plica \u00e0 Contesta\u00e7\u00e3o - Padr\u00e3o',
$$EXCELENT\u00cdSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA {{ processo.local_tramite or '___' }} VARA {{ (processo.area_atuacao or 'C\u00edvel') }} DA COMARCA DE {{ processo.comarca or '___' }}.

Processo: {{ processo.numero_cnj or processo.id_processo or '___' }}

{{ cliente.nome_completo or 'AUTOR' }}, por seu advogado, vem apresentar

R\u00c9PLICA \u00c0 CONTESTA\u00c7\u00c3O

nos termos abaixo.

I. S\u00cdNTESE DA CONTESTA\u00c7\u00c3O
{{ content.fatos or '[Resumo dos argumentos da contesta\u00e7\u00e3o]' }}

II. IMPUGNA\u00c7\u00c3O ESPEC\u00cdFICA
{{ content.fundamentos or '[Impugna\u00e7\u00e3o \u00e0s preliminares e ao m\u00e9rito]' }}

III. REITERA\u00c7\u00c3O DOS PEDIDOS
{{ content.pedidos or '[Reiterar pedidos e requerimentos]' }}

IV. PROVAS
{{ content.provas or '[Provas e requerimentos de instru\u00e7\u00e3o]' }}

V. REQUERIMENTOS FINAIS
Requer-se o recebimento da presente r\u00e9plica, com o prosseguimento do feito.

{{ content.local_data_assinatura or (processo.comarca or 'Cidade') ~ ', ' ~ hoje }}

____________________________________
{{ advogado.nome_completo or 'ADVOGADO' }}
OAB {{ advogado.oab or advogado.advogado_oab or '___' }}
$$,
  true
)
ON CONFLICT (tenant_id, code) DO UPDATE
SET title = EXCLUDED.title,
    body_jinja = EXCLUDED.body_jinja,
    is_active = true,
    updated_at = now();
"""

    op.execute(sa.text(replica_seed_sql))


def downgrade() -> None:
    op.drop_table("petition_versions")
    op.drop_table("petition_templates")
