from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.services.cadastro_service import CadastroService

escritorio_bp = Blueprint('escritorio', __name__, url_prefix='/escritorio')
service = CadastroService()

@escritorio_bp.route('/ui/painel')
@login_required
def painel_escritorio():
    dados = service.get_escritorio() or {}
    advs = service.list_advogados()
    return render_template('escritorio_painel.html', escritorio=dados, advogados=advs)

@escritorio_bp.route('/ui/escritorio/salvar', methods=['POST'])
@login_required
def salvar_escritorio():
    form = request.form.to_dict(flat=True)
    telefones = [t.strip() for t in (form.get('telefones') or '').split(';') if t.strip()]
    responsaveis = [r.strip() for r in (form.get('responsaveis') or '').split(';') if r.strip()]
    areas_raw = [a.strip() for a in (form.get('areas') or '').split(';') if a.strip()]
    areas = {a: True for a in areas_raw}
    payload = {
        'razao_social': form.get('razao_social'),
        'nome_fantasia': form.get('nome_fantasia'),
        'cnpj': form.get('cnpj'),
        'endereco_completo': form.get('endereco_completo'),
        'telefones': telefones,
        'email_contato': form.get('email_contato'),
        'site': form.get('site'),
        'responsaveis': responsaveis,
        'areas_atuacao': areas
    }
    service.save_escritorio(payload)
    dados = service.get_escritorio() or {}
    return render_template('_escritorio_dados.html', escritorio=dados)

@escritorio_bp.route('/ui/advogados/novo', methods=['POST'])
@login_required
def novo_advogado():
    form = request.form.to_dict(flat=True)
    service.save_advogado(form)
    advs = service.list_advogados()
    return render_template('_lista_advogados.html', advogados=advs)

@escritorio_bp.route('/ui/advogados/novo/form', methods=['GET'])
@login_required
def novo_advogado_form():
    return render_template('_advogado_form.html', adv=None)

@escritorio_bp.route('/ui/advogados/<oab>/delete', methods=['DELETE'])
@login_required
def del_advogado(oab):
    service.delete_advogado(oab)
    advs = service.list_advogados()
    return render_template('_lista_advogados.html', advogados=advs)

@escritorio_bp.route('/ui/advogados/<oab>/editar', methods=['GET'])
@login_required
def editar_advogado_form(oab):
    adv = service.get_advogado(oab)
    return render_template('_advogado_form.html', adv=adv)

@escritorio_bp.route('/ui/advogados/<oab>/update', methods=['POST'])
@login_required
def update_advogado(oab):
    form = request.form.to_dict(flat=True)
    # Permite mudança de OAB; passa oab_original
    service.save_advogado(form, oab_original=oab)
    advs = service.list_advogados()
    # Retorna lista e reseta formulário de cadastro (swap OOB)
    lista_html = render_template('_lista_advogados.html', advogados=advs)
    form_html = render_template('_advogado_form.html', adv=None)
    return lista_html + f"\n<div id='advogado-form-wrapper' hx-swap-oob='true'>{form_html}</div>"

@escritorio_bp.route('/api/advogados', methods=['GET'])
@login_required
def api_list_advogados():
    return jsonify(service.list_advogados())
