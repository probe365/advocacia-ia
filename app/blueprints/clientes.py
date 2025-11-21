from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required
from app.services.cadastro_service import CadastroService

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')
service = CadastroService()

@clientes_bp.route('/')
@login_required
def list_clientes_ui():
    clientes = service.list_clientes()
    return render_template('clientes.html', clientes=clientes)

@clientes_bp.route('/api', methods=['GET'])
def list_clientes_api():
    return jsonify(service.list_clientes())

@clientes_bp.route('/api', methods=['POST'])
def create_cliente_api():
    dados = request.get_json() or {}
    if not dados.get('nome_completo'):
        return jsonify({'erro':'nome_completo requerido'}), 400
    new_id = service.create_cliente(dados)
    dados['id_cliente'] = new_id
    return jsonify({'mensagem':'Cliente criado', 'cliente':dados}), 201

# --- UI (compatibility) endpoints replicating old /ui paths but without internal HTTP calls ---
@clientes_bp.route('/ui', methods=['GET'])
def ui_mostrar_clientes():
    clientes = service.list_clientes()
    return render_template('clientes.html', clientes=clientes)

@clientes_bp.route('/ui/form', methods=['GET'])
def ui_get_form():
    return render_template('_form_cliente.html', modal_title='Adicionar Novo Cliente')

@clientes_bp.route('/ui/novo', methods=['POST'])
def ui_create_cliente():
    form_data = request.form.to_dict()
    service.create_cliente(form_data)
    clientes = service.list_clientes()
    return render_template('_cards_cliente.html', clientes=clientes)

@clientes_bp.route('/ui/<id_cliente>/editform', methods=['GET'])
def ui_edit_form(id_cliente):
    cliente = service.get_cliente(id_cliente)
    return render_template('_form_cliente.html', cliente=cliente, modal_title='Editar Cliente')

@clientes_bp.route('/ui/<id_cliente>/edit', methods=['POST'])
def ui_edit_cliente(id_cliente):
    form_data = request.form.to_dict()
    service.update_cliente(id_cliente, form_data)
    clientes = service.list_clientes()
    return render_template('_cards_cliente.html', clientes=clientes)

@clientes_bp.route('/api/<id_cliente>', methods=['DELETE'])
def delete_cliente_api(id_cliente):
    ok = service.delete_cliente(id_cliente)
    if ok:
        return '', 200
    return jsonify({'erro':'Cliente não encontrado'}), 404
