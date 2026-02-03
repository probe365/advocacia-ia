# app/blueprints/petitions.py
import re

from flask import Blueprint, flash, json, redirect, request, render_template, g, abort, make_response, send_file, url_for
from flask_login import login_required, current_user
from io import BytesIO

from app.services.petition_service import PetitionService
from cadastro_manager import CadastroManager
from pipeline import Pipeline

from flask import send_file
import io

petitions_bp = Blueprint("petitions", __name__, url_prefix="/petitions")
service = PetitionService()


@petitions_bp.route("/partial/list")
@login_required
def partial_list():
    process_id = (request.args.get("process_id") or "").strip()
    if not process_id:
        abort(400, "process_id é obrigatório")

    petitions = service.list_by_process(tenant_id=g.tenant_id, process_id=process_id)

    view = (request.args.get("view") or "").strip().lower()
    if view == "pills":
        return render_template("petitions/_list_pills.html", petitions=petitions)

    return render_template("petitions/_list.html", petitions=petitions)

@petitions_bp.route("/partial/strip")
@login_required
def partial_strip():
    process_id = (request.args.get("process_id") or "").strip()
    if not process_id:
        abort(400, "process_id é obrigatório")

    petitions = service.list_by_process(tenant_id=g.tenant_id, process_id=process_id)
    return render_template("petitions/_strip.html", petitions=petitions)



@petitions_bp.route("/create", methods=["POST"])
@login_required
def create():
    process_id = (request.form.get("process_id") or "").strip()
    petition_type = (request.form.get("petition_type") or "").strip().lower()

    if not process_id or petition_type not in {"inicial", "contestacao", "replica"}:
        abort(400, "process_id ou petition_type inválidos")

    petition_id = service.create_or_get_petition(
        tenant_id=g.tenant_id,
        user_id=current_user.id,
        process_id=process_id,
        petition_type=petition_type,
    )

    service.apply_model_text_if_empty(g.tenant_id, petition_id)

    try:
        service.seed_content_from_context(g.tenant_id, petition_id, force=False)
    except Exception:
        pass

    # ✅ retorna SOMENTE a faixa horizontal
    petitions = service.list_by_process(g.tenant_id, process_id)
    html = render_template("petitions/_strip.html", petitions=petitions)

    resp = make_response(html)
    resp.headers["HX-Trigger"] = json.dumps({
        "openPetition": {"id": petition_id}
    })
    return resp

@petitions_bp.route("/<int:petition_id>/apply-firac", methods=["POST"])
@login_required
def apply_firac(petition_id):
    tenant_id = g.tenant_id

    petition = service.get_petition(tenant_id, petition_id)
    if not petition:
        abort(404)

    process_id = petition["process_id"]

    # 🔹 buscar FIRAC salvo (com fallback de process_id)
    firac = service.get_firac_by_process(tenant_id, process_id)

    if not firac:
        # fallback: tenta carregar FIRAC do cache/pipeline
        try:
            pipeline = Pipeline(case_id=process_id, tenant_id=tenant_id)
            result = pipeline.generate_firac()
            firac = result.get("data") if isinstance(result, dict) else None
            def _as_text(value):
                if isinstance(value, list):
                    try:
                        return json.dumps(value, ensure_ascii=False)
                    except Exception:
                        return "\n".join([str(v) for v in value if v is not None])
                return str(value or "")

            if firac:
                CadastroManager(tenant_id).upsert_process_firac(
                    process_id=process_id,
                    facts=_as_text(firac.get("facts")),
                    issue=_as_text(firac.get("issue")),
                    rules=_as_text(firac.get("rules")),
                    application=_as_text(firac.get("application")),
                    conclusion=_as_text(firac.get("conclusion")),
                    created_by_user_id=int(current_user.get_id()),
                    source="pipeline",
                )
        except Exception:
            firac = None

    if not firac:
        petition = service.get_petition(tenant_id, petition_id)
        versions = service.list_versions(tenant_id, petition_id)
        return render_template(
            "petitions/_editor.html",
            petition=petition,
            versions=versions,
            warning_message="Gere o FIRAC antes de aplicar à petição.",
        )

    service.apply_firac_autofill(
        tenant_id=g.tenant_id,
        petition_id=petition_id,
        firac_data=firac,
        force=True,
    )

    # Gera texto completo com a lógica do petition_module (Pipeline)
    try:
        ctx = service.preparar_contexto_peticao(tenant_id, process_id) or {}
        proc = ctx.get("processo") or {}
        autor = ctx.get("autor") or {}
        reu = ctx.get("reu") or {}
        advogado = ctx.get("advogado") or {}

        adv_oab_raw = (advogado.get("oab") or advogado.get("advogado_oab") or "").strip()
        oab_uf = "XX"
        oab_num = adv_oab_raw
        m = re.match(r"([A-Za-z]{2})\s*-?\s*(.*)", adv_oab_raw)
        if m:
            oab_uf = m.group(1).upper()
            oab_num = m.group(2).strip()

        def _extract_uf(*values: str) -> str:
            for val in values:
                txt = (val or "").upper()
                m = re.search(r"\b([A-Z]{2})\b", txt)
                if m:
                    return m.group(1)
            return "XX"

        juizo_vara = (
            proc.get("vara")
            or proc.get("local_tramite")
            or ""
        )
        juizo_comarca = proc.get("comarca") or ""
        juizo_uf = _extract_uf(proc.get("uf"), juizo_comarca, juizo_vara)

        dados_ui = {
            "juizo": {
                "vara": juizo_vara,
                "especialidade": (proc.get("area_atuacao") or "Cível").upper(),
                "comarca": juizo_comarca,
                "uf": juizo_uf,
            },
            "autor": {
                "nome_completo_ou_razao_social": autor.get("nome_completo") or autor.get("nome") or "AUTOR",
                "cpf": autor.get("cpf_cnpj") or autor.get("cpf") or "",
                "endereco": autor.get("endereco_completo") or autor.get("endereco") or "",
                "email": autor.get("email") or "",
            },
            "reu": {
                "nome": reu.get("nome_completo") or reu.get("nome") or "RÉU",
                "cpf_cnpj": reu.get("cpf_cnpj") or reu.get("cpf") or "",
                "endereco": reu.get("endereco_completo") or reu.get("endereco") or "",
                "email": reu.get("email") or "",
            },
            "advogado": {
                "nome": advogado.get("nome") or advogado.get("nome_completo") or "",
                "oab_uf": oab_uf,
                "oab_numero": oab_num,
                "email": advogado.get("email") or "",
            },
            "outros": {
                "valor_causa_num": proc.get("valor_causa") or "",
                "valor_causa_ext": "",
                "texto_provas_especificas": "",
            },
        }

        def _as_text(value):
            if isinstance(value, list):
                return "\n".join([str(v) for v in value if v is not None])
            return str(value or "")

        firac_payload = {
            "facts": _as_text(firac.get("facts")),
            "issue": _as_text(firac.get("issue")),
            "rules": _as_text(firac.get("rules")),
            "application": _as_text(firac.get("application")),
            "conclusion": _as_text(firac.get("conclusion")),
        }

        pipeline = Pipeline(case_id=process_id, tenant_id=tenant_id)
        texto_completo = pipeline.generate_peticao_rascunho(dados_ui, firac_payload)
        if texto_completo:
            service.save_petition_content(
                tenant_id=tenant_id,
                petition_id=petition_id,
                content_updates={"texto_livre": texto_completo},
            )
    except Exception:
        pass

    petition = service.get_petition(tenant_id, petition_id)
    versions = service.list_versions(tenant_id, petition_id)

    return render_template(
        "petitions/_editor.html",
        petition=petition,
        versions=versions
    )


@petitions_bp.route("/<int:petition_id>/partial/editor")
@login_required
def partial_editor(petition_id: int):
    petition = service.get_petition(tenant_id=g.tenant_id, petition_id=petition_id)
    if not petition:
        abort(404)

    # 1) Se existir FIRAC salvo para o processo, preenche blocos + rerender texto_livre
    try:
        service.autofill_petition_from_firac_if_possible(g.tenant_id, petition_id, force=False)
    except Exception:
        pass

    # 2) Recarrega após possível update
    petition = service.get_petition(g.tenant_id, petition_id)

    # 3) Se ainda estiver vazio (petição antiga/sem FIRAC), usa seu autofill antigo
    if not (petition.get("content") or {}).get("texto_livre", "").strip():
        service.autofill_petition_text(g.tenant_id, petition_id)
        petition = service.get_petition(g.tenant_id, petition_id)

    versions = service.list_versions(tenant_id=g.tenant_id, petition_id=petition_id)
    return render_template("petitions/_editor.html", petition=petition, versions=versions)


@petitions_bp.route("/<int:petition_id>/apply-template", methods=["POST"])
@login_required
def apply_template(petition_id: int):
    # force=True: sobrescreve o texto atual quando o usuário pedir
    service.apply_model_text_if_empty(
        tenant_id=g.tenant_id,
        petition_id=petition_id,
        force=True,
    )

    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)

    resp = make_response(render_template("petitions/_editor.html", petition=petition, versions=versions))
    resp.headers["HX-Trigger"] = json.dumps({"petitionStatus": {"value": petition.get("status")}})
    return resp


@petitions_bp.route("/<int:petition_id>/save", methods=["POST"])
@login_required
def save(petition_id: int):
    payload = {
        "texto_livre": request.form.get("texto_livre", ""),

        "enderecamento": request.form.get("enderecamento", ""),
        "tipo_acao": request.form.get("tipo_acao", ""),
        "fatos": request.form.get("fatos", ""),
        "fundamentos": request.form.get("fundamentos", ""),
        "pedidos": request.form.get("pedidos", ""),
        "provas": request.form.get("provas", ""),
        "local_data_assinatura": request.form.get("local_data_assinatura", ""),
    }

    service.save_petition_content(
        tenant_id=g.tenant_id,
        petition_id=petition_id,
        content_updates=payload,
    )

    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)

    resp = make_response(render_template("petitions/_editor.html", petition=petition, versions=versions))
    resp.headers["HX-Trigger"] = json.dumps({"petitionStatus": {"value": petition.get("status")}})
    return resp


@petitions_bp.route("/<int:petition_id>/render", methods=["POST"])
@login_required
def render(petition_id: int):
    service.render_from_template(
        tenant_id=g.tenant_id,
        user_id=int(current_user.get_id()),
        petition_id=petition_id,
    )

    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)
    return render_template("petitions/_editor.html", petition=petition, versions=versions)


@petitions_bp.route("/<int:petition_id>/partial/versions")
@login_required
def partial_versions(petition_id: int):
    versions = service.list_versions(g.tenant_id, petition_id)
    return render_template("petitions/_versions.html", versions=versions)


@petitions_bp.route("/<int:petition_id>/finalize", methods=["POST"])
@login_required
def finalize(petition_id: int):
    service.finalize_petition(g.tenant_id, petition_id)
    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)

    resp = make_response(render_template("petitions/_editor.html", petition=petition, versions=versions))
    resp.headers["HX-Trigger"] = json.dumps({"petitionStatus": {"value": petition.get("status")}})
    return resp




@petitions_bp.route("/<int:petition_id>/export/docx")
@login_required
def export_docx(petition_id: int):
    data = service.build_docx_bytes(tenant_id=g.tenant_id, petition_id=petition_id)

    # nome amigável
    petition = service.get_petition(g.tenant_id, petition_id)
    ptype = (petition.get("petition_type") if petition else "peticao") or "peticao"
    filename = f"{ptype}_{petition_id}.docx".replace(" ", "_")

    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

@petitions_bp.route("/<int:petition_id>/draft", methods=["POST"])
@login_required
def mark_draft(petition_id: int):
    service.mark_draft(g.tenant_id, petition_id)
    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)
    return render_template("petitions/_editor.html", petition=petition, versions=versions)

@petitions_bp.route("/<int:petition_id>/set-status/<status>", methods=["POST"])
@login_required
def set_status(petition_id: int, status: str):
    service.set_status(g.tenant_id, petition_id, status)
    petition = service.get_petition(g.tenant_id, petition_id)
    versions = service.list_versions(g.tenant_id, petition_id)
    return render_template("petitions/_editor.html", petition=petition, versions=versions)
