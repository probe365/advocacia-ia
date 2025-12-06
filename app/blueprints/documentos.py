from flask import Blueprint, jsonify, request, render_template, flash
from werkzeug.utils import secure_filename
from pipeline import Pipeline
import logging

bp = Blueprint('documentos', __name__)
logger = logging.getLogger(__name__)

@bp.route('/api/v1/processos/<id_processo>/documentos', methods=['POST'])
def upload_documento(id_processo: str):
    if 'file' not in request.files:
        return jsonify({'erro':'Nenhum arquivo enviado.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'erro':'Nenhum arquivo selecionado.'}), 400
    try:
        filename = secure_filename(file.filename)
        file_bytes = file.read()
        from pathlib import Path
        import openai
        from ingestion_module import IngestionHandler
        base_cases_dir = Path("./cases")
        openai_client = openai.OpenAI()
        ingestion_handler = IngestionHandler(
            nlp_processor=None,
            text_splitter=None,
            label_map=None,
            case_store=None,
            kb_store=None
        )
        pipeline = Pipeline(
            case_id=id_processo,
            ingestion_handler=ingestion_handler,
            openai_client=openai_client,
            base_cases_dir=base_cases_dir,
            tenant_id=None
        )
        resultado = pipeline.processar_upload_de_arquivo(id_processo, filename, file_bytes)
        status = 200 if resultado.get('status') == 'sucesso' else 500
        return jsonify(resultado), status
    except Exception as e:
        logger.exception('Erro upload')
        return jsonify({'erro':f'Interno: {e}'}), 500

@bp.route('/api/v1/processos/<id_processo>/documentos', methods=['GET'])
def listar_documentos(id_processo: str):
    try:
        from pathlib import Path
        import openai
        from ingestion_module import IngestionHandler
        base_cases_dir = Path("./cases")
        openai_client = openai.OpenAI()
        ingestion_handler = IngestionHandler(
            nlp_processor=None,
            text_splitter=None,
            label_map=None,
            case_store=None,
            kb_store=None
        )
        pipeline = Pipeline(
            case_id=id_processo,
            ingestion_handler=ingestion_handler,
            openai_client=openai_client,
            base_cases_dir=base_cases_dir,
            tenant_id=None
        )
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
    try:
        from pathlib import Path
        import openai
        from ingestion_module import IngestionHandler
        base_cases_dir = Path("./cases")
        openai_client = openai.OpenAI()
        ingestion_handler = IngestionHandler(
            nlp_processor=None,
            text_splitter=None,
            label_map=None,
            case_store=None,
            kb_store=None
        )
        pipeline = Pipeline(
            case_id=id_processo,
            ingestion_handler=ingestion_handler,
            openai_client=openai_client,
            base_cases_dir=base_cases_dir,
            tenant_id=None
        )
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
        from pathlib import Path
        import openai
        from ingestion_module import IngestionHandler
        base_cases_dir = Path("./cases")
        openai_client = openai.OpenAI()
        ingestion_handler = IngestionHandler(
            nlp_processor=None,
            text_splitter=None,
            label_map=None,
            case_store=None,
            kb_store=None
        )
        pipeline = Pipeline(
            case_id=id_processo,
            ingestion_handler=ingestion_handler,
            openai_client=openai_client,
            base_cases_dir=base_cases_dir,
            tenant_id=None
        )
        pipeline.delete_document_by_filename(filename)
        docs = pipeline.list_unique_case_documents()
        return render_template('_lista_documentos.html', documentos=docs)
    except Exception as e:
        logger.exception('Erro delete UI')
        return f"<div class='alert alert-danger'>Erro excluir: {e}</div>"
