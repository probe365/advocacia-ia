from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, g
from flask_login import login_required
from app.services.cadastro_service import CadastroService

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

# Helper function to get service with proper tenant_id
def get_service():
    from cadastro_manager import CadastroManager
    tenant_id = getattr(g, 'tenant_id', None)
    manager = CadastroManager(tenant_id=tenant_id)
    return CadastroService(manager=manager)

@clientes_bp.route('/')
@login_required
def list_clientes_ui():
    service = get_service()
    clientes = service.list_clientes()
    return render_template('clientes.html', clientes=clientes)

@clientes_bp.route('/api', methods=['GET'])
def list_clientes_api():
    service = get_service()
    return jsonify(service.list_clientes())

@clientes_bp.route('/api', methods=['POST'])
def create_cliente_api():
    service = get_service()
    dados = request.get_json() or {}
    if not dados.get('nome_completo'):
        return jsonify({'erro':'nome_completo requerido'}), 400
    new_id = service.create_cliente(dados)
    dados['id_cliente'] = new_id
    return jsonify({'mensagem':'Cliente criado', 'cliente':dados}), 201

# --- UI (compatibility) endpoints replicating old /ui paths but without internal HTTP calls ---
@clientes_bp.route('/ui', methods=['GET'])
def ui_mostrar_clientes():
    service = get_service()
    clientes = service.list_clientes()
    return render_template('clientes.html', clientes=clientes)

@clientes_bp.route('/ui/form', methods=['GET'])
def ui_get_form():
    return render_template('_form_cliente.html', modal_title='Adicionar Novo Cliente')

@clientes_bp.route('/ui/novo', methods=['POST'])
def ui_create_cliente():
    service = get_service()
    form_data = request.form.to_dict()
    service.create_cliente(form_data)
    clientes = service.list_clientes()
    return render_template('_cards_cliente.html', clientes=clientes)

@clientes_bp.route('/ui/<id_cliente>/editform', methods=['GET'])
def ui_edit_form(id_cliente):
    service = get_service()
    cliente = service.get_cliente(id_cliente)
    return render_template('_form_cliente.html', cliente=cliente, modal_title='Editar Cliente')

@clientes_bp.route('/ui/<id_cliente>/edit', methods=['POST'])
def ui_edit_cliente(id_cliente):
    service = get_service()
    form_data = request.form.to_dict()
    service.update_cliente(id_cliente, form_data)
    clientes = service.list_clientes()
    return render_template('_cards_cliente.html', clientes=clientes)

@clientes_bp.route('/api/<id_cliente>', methods=['DELETE'])
def delete_cliente_api(id_cliente):
    service = get_service()
    ok = service.delete_cliente(id_cliente)
    if ok:
        return '', 200
    return jsonify({'erro':'Cliente não encontrado'}), 404













