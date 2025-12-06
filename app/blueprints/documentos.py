from flask import Blueprint, jsonify, request, render_template, g
from werkzeug.utils import secure_filename
from pipeline import Pipeline
import logging

bp = Blueprint('documentos', __name__)
logger = logging.getLogger(__name__)


def _build_pipeline(case_id: str) -> Pipeline:
    """Instancia o Pipeline respeitando o tenant atual."""
    tenant_id = getattr(g, 'tenant_id', None)
    return Pipeline(case_id=case_id, tenant_id=tenant_id)

@bp.route('/api/v1/processos/<id_processo>/documentos', methods=['POST'])
def upload_documento(id_processo: str):
    if 'file' not in request.files:
        return jsonify({'erro':'Nenhum arquivo enviado.'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'erro':'Nenhum arquivo selecionado.'}), 400
    try:
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        pipeline = _build_pipeline(id_processo)
        resultado = pipeline.processar_upload_de_arquivo(id_processo, filename, file_bytes)
        status = 200 if resultado.get('status') == 'sucesso' else 500
        return jsonify(resultado), status
    except Exception as e:
        logger.exception('Erro upload')
        return jsonify({'erro':f'Interno: {e}'}), 500

@bp.route('/api/v1/processos/<id_processo>/documentos', methods=['GET'])
def listar_documentos(id_processo: str):
    try:
        pipeline = _build_pipeline(id_processo)
        docs = pipeline.list_unique_case_documents()
        return jsonify(docs)
    except Exception as e:
        logger.exception('Erro listar docs')
        return jsonify({'erro':'Falha interna'}), 500

# UI helpers
@bp.route('/processos/ui/<id_processo>/uploadform')
def ui_get_upload_form(id_processo):
    return render_template('_form_upload.html', id_processo=id_processo)

@bp.route('/processos/ui/<id_processo>/documentos/novo', methods=['POST'])
def ui_upload_documento(id_processo):
    if 'file' not in request.files:
        return "<div class='alert alert-danger'>Nenhum arquivo enviado.</div>"
    file = request.files['file']
    if not file.filename:
        return "<div class='alert alert-danger'>Nenhum arquivo selecionado.</div>"
    try:
        pipeline = _build_pipeline(id_processo)
        filename = secure_filename(file.filename)
        pipeline.processar_upload_de_arquivo(id_processo, filename, file.read())
        docs = pipeline.list_unique_case_documents()
        return render_template('_lista_documentos.html', documentos=docs)
    except Exception as e:
        logger.exception('Erro upload UI')
        return f"<div class='alert alert-danger'>Erro: {e}</div>"

@bp.route('/processos/ui/<id_processo>/documentos/<path:filename>', methods=['DELETE'])
def ui_delete_documento(id_processo, filename):
    try:
        pipeline = _build_pipeline(id_processo)
        pipeline.delete_document_by_filename(filename)
        docs = pipeline.list_unique_case_documents()
        return render_template('_lista_documentos.html', documentos=docs)
    except Exception as e:
        logger.exception('Erro delete UI')
        return f"<div class='alert alert-danger'>Erro excluir: {e}</div>"
