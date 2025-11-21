from flask import Blueprint, request, render_template
from flask_login import login_required
from pipeline import Pipeline
from werkzeug.utils import secure_filename
import os, logging, traceback, json
from pathlib import Path
from urllib.parse import unquote

kb_bp = Blueprint('kb', __name__, url_prefix='/kb')
logger = logging.getLogger(__name__)

_KB_PIPELINE_CACHE = None
FALLBACK_KB_DIR = Path('./kb_fallback')
FALLBACK_KB_DIR.mkdir(parents=True, exist_ok=True)
FALLBACK_INDEX = FALLBACK_KB_DIR / 'index.json'

def _load_fallback_index() -> list:
    if FALLBACK_INDEX.exists():
        try:
            return json.loads(FALLBACK_INDEX.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []

def _save_fallback_index(names: list):
    try:
        FALLBACK_INDEX.write_text(json.dumps(sorted(set(names))), encoding='utf-8')
    except Exception as e:
        logger.warning(f"Falha ao salvar fallback index: {e}")

def _fallback_store_file(filename: str, content: bytes):
    # Armazena o arquivo bruto apenas para referência futura
    safe_name = filename.replace('/', '_')
    target = FALLBACK_KB_DIR / safe_name
    try:
        target.write_bytes(content)
    except Exception as e:
        logger.error(f"Falha ao gravar fallback file {filename}: {e}")
    names = _load_fallback_index()
    names.append(filename)
    _save_fallback_index(names)

def _merged_kb_filenames(pipeline) -> list:
    base = []
    try:
        if pipeline:
            base = pipeline.get_global_kb_filenames() or []
    except Exception as e:
        logger.warning(f"Falha list kb pipeline: {e}")
    fallback = _load_fallback_index()
    merged = sorted(set(base + fallback))
    return merged

def _get_kb_pipeline(light: bool = True):
    global _KB_PIPELINE_CACHE
    if _KB_PIPELINE_CACHE is None:
        try:
            if light:
                # Inicialização leve: cria Pipeline e desativa componentes pesados não usados no upload
                p = Pipeline(case_id='kb_dummy')
                # Libera objetos não necessários para ingestão básica da KB
                try:
                    p.llm = None
                    p.agent_executor = None
                except Exception:
                    pass
                _KB_PIPELINE_CACHE = p
            else:
                _KB_PIPELINE_CACHE = Pipeline(case_id='kb_dummy')
        except Exception as e:
            logger.error(f"Falha ao inicializar Pipeline KB: {e}")
            raise
    return _KB_PIPELINE_CACHE

@kb_bp.route('/ui/painel', methods=['GET'])
@login_required
def kb_painel():
    # Lista simples de arquivos únicos na KB
    try:
        p = _get_kb_pipeline()  # usa para acessar kb_store
    except Exception as e:
        return f"<div class='alert alert-danger'>Erro inicializando KB: {e}</div>"
    filenames = _merged_kb_filenames(p)
    
    # Calcular estatísticas por tipo
    kb_stats = {'total': len(filenames), 'pdf': 0, 'image': 0, 'audio': 0, 'video': 0, 'text': 0}
    for f in filenames:
        ext = f.split('.')[-1].lower() if '.' in f else ''
        if ext == 'pdf':
            kb_stats['pdf'] += 1
        elif ext == 'txt':
            kb_stats['text'] += 1
        elif ext in ['jpg', 'jpeg', 'png', 'gif']:
            kb_stats['image'] += 1
        elif ext in ['mp3', 'wav']:
            kb_stats['audio'] += 1
        elif ext in ['mp4', 'mov']:
            kb_stats['video'] += 1
    
    return render_template('kb.html', kb_files=filenames, kb_stats=kb_stats)

@kb_bp.route('/ui/search', methods=['POST'])
@login_required
def kb_search():
    query = request.form.get('query', '').strip()
    if not query:
        return "<div class='alert alert-warning'>Digite uma consulta.</div>", 400
    
    try:
        p = _get_kb_pipeline()
        
        # Verificar se há documentos indexados
        total_docs = p.kb_store.get(include=[])
        total_chunks = len(total_docs.get("ids", []))
        
        if total_chunks == 0:
            fallback_count = len(_load_fallback_index())
            msg = f"""
            <div class='alert alert-warning'>
                <h6><i class='bi bi-exclamation-triangle'></i> Nenhum documento indexado no Chroma</h6>
                <p class='mb-1'>Total de arquivos no fallback: <strong>{fallback_count}</strong></p>
                <small>Documentos no fallback não podem ser buscados semanticamente. 
                Verifique se a OPENAI_API_KEY está configurada e tente fazer upload novamente.</small>
            </div>
            """
            return msg
        
        # Busca semântica usando Chroma similarity_search_with_score
        results_raw = p.kb_store.similarity_search_with_score(query, k=10)
        
        # Formatar resultados
        results = []
        for doc, score in results_raw:
            text = doc.page_content
            
            # Fix encoding: texto tem escape sequences literais como "\xc3\xa9"
            if '\\x' in text:
                try:
                    # Converter string com escapes literais para bytes reais e decodificar UTF-8
                    text = text.encode('latin1').decode('unicode_escape').encode('latin1').decode('utf-8')
                except Exception:
                    try:
                        # Fallback: caracteres corrompidos tipo "Ã©"
                        text = text.encode('latin1').decode('utf-8')
                    except Exception:
                        pass  # Manter original
            # Se não tem \x mas tem caracteres corrompidos tipo "Ã©"
            elif any(bad in text for bad in ['Ã©', 'Ã§', 'Ã£', 'Ãµ', 'Ã¡', 'Ãº', 'Ã­', 'Ã³']):
                try:
                    text = text.encode('latin1').decode('utf-8')
                except Exception:
                    pass  # Manter original
            
            results.append({
                'text': text,
                'filename': doc.metadata.get('filename', 'Desconhecido'),
                'source': doc.metadata.get('source', ''),
                'type': doc.metadata.get('type', ''),
                'score': 1 - score  # Chroma retorna distância, convertemos para similaridade
            })
        
        logger.info(f"Busca KB: '{query}' retornou {len(results)} resultados de {total_chunks} chunks totais")
        return render_template('_kb_search_results.html', results=results, query=query)
    
    except Exception as e:
        logger.error(f"Erro na busca KB: {e}")
        trace = traceback.format_exc(limit=3)
        return f"<div class='alert alert-danger'>Erro na busca: {e}<pre class='small'>{trace}</pre></div>", 500

@kb_bp.route('/ui/clear-search', methods=['GET'])
@login_required
def kb_clear_search():
    return ""  # Retorna vazio para limpar a div de resultados

@kb_bp.route('/ui/view/<path:filename>', methods=['GET'])
@login_required
def kb_view_document(filename):
    """Visualiza o conteúdo completo de um documento da KB."""
    from urllib.parse import unquote
    filename = unquote(filename)
    
    try:
        p = _get_kb_pipeline()
        
        # Buscar todos os chunks deste arquivo
        results = p.kb_store.get(
            where={"filename": filename},
            include=["metadatas", "documents"]
        )
        
        documents = results.get("documents", [])
        
        if not documents:
            # Tentar fallback
            safe_name = filename.replace('/', '_')
            fallback_file = FALLBACK_KB_DIR / safe_name
            
            if fallback_file.exists():
                try:
                    content = fallback_file.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    content = fallback_file.read_text(encoding='iso-8859-1', errors='ignore')
                
                return render_template('_kb_view_document.html', 
                                     filename=filename, 
                                     content=content,
                                     from_fallback=True)
            else:
                return "<div class='alert alert-danger'>Documento não encontrado.</div>", 404
        
        # Concatenar todos os chunks
        full_content = "\n\n".join(documents)
        
        # Fix encoding: texto tem escape sequences literais como "\xc3\xa9"
        if '\\x' in full_content:
            try:
                # Converter string com escapes literais para bytes reais e decodificar UTF-8
                # Exemplo: "\\xc3\\xa9" -> b'\xc3\xa9' -> "é"
                full_content = full_content.encode('latin1').decode('unicode_escape').encode('latin1').decode('utf-8')
                logger.info(f"Encoding corrigido (escape sequences) para '{filename}'")
            except Exception as e:
                logger.warning(f"Método 1 falhou, tentando alternativa: {e}")
                try:
                    # Se texto tem caracteres corrompidos tipo "Ã©"
                    full_content = full_content.encode('latin1').decode('utf-8')
                    logger.info(f"Encoding corrigido (latin1->utf8) para '{filename}'")
                except Exception as e2:
                    logger.warning(f"Não foi possível corrigir encoding: {e2}")
        
        # Se não tem \x mas tem caracteres corrompidos tipo "Ã©"
        elif any(bad in full_content for bad in ['Ã©', 'Ã§', 'Ã£', 'Ãµ', 'Ã¡', 'Ãº', 'Ã­', 'Ã³']):
            try:
                full_content = full_content.encode('latin1').decode('utf-8')
                logger.info(f"Encoding corrigido (latin1->utf8) para '{filename}'")
            except Exception as e:
                logger.warning(f"Não foi possível corrigir encoding: {e}")
        
        return render_template('_kb_view_document.html', 
                             filename=filename, 
                             content=full_content,
                             from_fallback=False,
                             total_chunks=len(documents))
    
    except Exception as e:
        logger.error(f"Erro ao visualizar documento '{filename}': {e}", exc_info=True)
        return f"<div class='alert alert-danger'>Erro ao carregar documento: {e}</div>", 500

@kb_bp.route('/ui/debug/<path:filename>', methods=['GET'])
@login_required
def kb_debug_file(filename):
    """Endpoint de debug para verificar se arquivo está indexado no Chroma."""
    from urllib.parse import unquote
    filename = unquote(filename)
    
    try:
        p = _get_kb_pipeline()
        
        # Buscar todos os chunks deste arquivo
        results = p.kb_store.get(
            where={"filename": filename},
            include=["metadatas", "documents"]
        )
        
        ids = results.get("ids", [])
        metadatas = results.get("metadatas", [])
        documents = results.get("documents", [])
        
        debug_info = {
            "filename": filename,
            "total_chunks": len(ids),
            "chunks": []
        }
        
        for i, doc_id in enumerate(ids):
            debug_info["chunks"].append({
                "id": doc_id,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "content_preview": documents[i][:200] if i < len(documents) else ""
            })
        
        # Verificar fallback
        fallback_names = _load_fallback_index()
        debug_info["in_fallback"] = filename in fallback_names
        
        html = f"""
        <div class="alert alert-info">
            <h5>Debug: {filename}</h5>
            <ul>
                <li><strong>Chunks no Chroma:</strong> {debug_info['total_chunks']}</li>
                <li><strong>No Fallback:</strong> {'Sim' if debug_info['in_fallback'] else 'Não'}</li>
            </ul>
        </div>
        """
        
        if debug_info['total_chunks'] > 0:
            html += "<h6>Preview dos chunks:</h6><ul class='small'>"
            for chunk in debug_info['chunks'][:5]:  # Mostrar apenas 5 primeiros
                html += f"<li><code>{chunk['id']}</code>: {chunk['content_preview']}...</li>"
            html += "</ul>"
        else:
            html += """<div class='alert alert-warning'>
                <strong><i class='bi bi-exclamation-triangle'></i> Arquivo NÃO está indexado no Chroma!</strong><br>
                Apenas no fallback (sem busca semântica).<br><br>
            """
            
            if debug_info['in_fallback']:
                html += f"""
                <button class='btn btn-primary btn-sm' onclick='reindexFile("{filename}")'>
                    <i class='bi bi-arrow-repeat'></i> Re-indexar Agora
                </button>
                <div id='reindex-result-{hash(filename)}'></div>
                """
            
            html += "</div>"
        
        return html
    
    except Exception as e:
        logger.error(f"Erro debug KB: {e}", exc_info=True)
        return f"<div class='alert alert-danger'>Erro: {e}</div>", 500

@kb_bp.route('/ui/reindex/<path:filename>', methods=['POST'])
@login_required
def kb_reindex_file(filename):
    """Re-indexa um arquivo que está apenas no fallback."""
    from urllib.parse import unquote
    filename = unquote(filename)
    
    try:
        p = _get_kb_pipeline()
        
        # Verificar se arquivo existe no fallback
        safe_name = filename.replace('/', '_')
        fallback_file = FALLBACK_KB_DIR / safe_name
        
        if not fallback_file.exists():
            return "<div class='alert alert-danger'>Arquivo não encontrado no fallback.</div>", 404
        
        # Ler conteúdo do arquivo
        content = fallback_file.read_bytes()
        ext = os.path.splitext(filename)[1].lower()
        
        # Processar baseado no tipo
        no_api_key = not os.getenv('OPENAI_API_KEY')
        if no_api_key:
            return """<div class='alert alert-danger'>
                <strong>OPENAI_API_KEY não configurada!</strong><br>
                Configure a chave de API do OpenAI para permitir indexação com embeddings.
            </div>""", 400
        
        try:
            if ext == '.pdf':
                p.ingestion_handler.add_pdf_kb(content, source_name=filename)
            elif ext == '.txt':
                p.ingestion_handler.add_text_kb(content, source_name=filename)
            elif ext in ['.jpg', '.jpeg', '.png']:
                p.ingestion_handler.add_image_kb(content, source_name=filename)
            elif ext in ['.mp3', '.wav']:
                p.ingestion_handler.add_audio_kb(content, source_name=filename, audio_format_suffix=ext, openai_client=p.openai_client)
            elif ext in ['.mp4', '.mov']:
                p.ingestion_handler.add_video_kb(content, source_name=filename, video_format_suffix=ext, openai_client=p.openai_client)
            else:
                return f"<div class='alert alert-warning'>Tipo não suportado: {ext}</div>", 400
            
            # Verificar se foi indexado com sucesso
            results = p.kb_store.get(where={"filename": filename}, include=[])
            chunks_count = len(results.get("ids", []))
            
            if chunks_count > 0:
                logger.info(f"Arquivo '{filename}' re-indexado com sucesso: {chunks_count} chunks")
                return f"""<div class='alert alert-success'>
                    <i class='bi bi-check-circle'></i> <strong>Re-indexação concluída!</strong><br>
                    Arquivo '{filename}' agora tem <strong>{chunks_count} chunks</strong> indexados.<br>
                    <small>Agora você pode fazer buscas semânticas neste arquivo.</small>
                </div>"""
            else:
                return "<div class='alert alert-warning'>Re-indexação não gerou chunks. Verifique o conteúdo do arquivo.</div>"
        
        except Exception as e:
            logger.error(f"Erro ao re-indexar '{filename}': {e}", exc_info=True)
            trace = traceback.format_exc(limit=3)
            return f"""<div class='alert alert-danger'>
                Erro ao re-indexar: {e}
                <details class='small'><summary>Detalhes</summary><pre>{trace}</pre></details>
            </div>""", 500
    
    except Exception as e:
        logger.error(f"Erro geral re-index: {e}", exc_info=True)
        return f"<div class='alert alert-danger'>Erro: {e}</div>", 500

@kb_bp.route('/ui/upload', methods=['POST'])
@login_required
def kb_upload():
    try:
        p = _get_kb_pipeline()
    except Exception as e_init:
        trace = traceback.format_exc(limit=3)
        return f"<div class='alert alert-danger p-2'>Falha init Pipeline KB: {e_init}<pre class='small mb-0'>{trace}</pre></div>", 500
    f = request.files.get('file')
    if not f:
        return "<div class='alert alert-danger p-2'>Arquivo não enviado.</div>", 400
    filename = secure_filename(f.filename)
    content = f.read()
    ext = os.path.splitext(filename)[1].lower()
    added_type = None
    # Se não houver chave OpenAI, faz fallback direto (evita travar em embeddings)
    no_api_key = not os.getenv('OPENAI_API_KEY')
    try:
        if not no_api_key:
            if ext == '.pdf':
                p.ingestion_handler.add_pdf_kb(content, source_name=filename)
                added_type = 'pdf'
            elif ext == '.txt':
                p.ingestion_handler.add_text_kb(content, source_name=filename)
                added_type = 'text'
            elif ext in ['.jpg', '.jpeg', '.png']:
                p.ingestion_handler.add_image_kb(content, source_name=filename)
                added_type = 'image'
            elif ext in ['.mp3', '.wav']:
                p.ingestion_handler.add_audio_kb(content, source_name=filename, audio_format_suffix=ext, openai_client=p.openai_client)
                added_type = 'audio'
            elif ext in ['.mp4', '.mov']:
                p.ingestion_handler.add_video_kb(content, source_name=filename, video_format_suffix=ext, openai_client=p.openai_client)
                added_type = 'video'
            else:
                return f"<div class='alert alert-warning p-2'>Tipo não suportado: {ext}</div>", 400
        if no_api_key:
            _fallback_store_file(filename, content)
            added_type = added_type or ext.lstrip('.') or 'file'
            warn = "<div class='alert alert-warning p-2 mb-2'>Sem OPENAI_API_KEY: arquivo salvo em fallback (não indexado em embeddings).</div>"
        else:
            warn = ''
        files = _merged_kb_filenames(p)
        html_list = render_template('_lista_kb.html', kb_files=files)
        msg = f"<div class='alert alert-success p-2 mb-2'>Arquivo '{filename}' ({added_type}) adicionado à KB.</div>"
        return warn + msg + html_list
    except Exception as e:
        # Último recurso: fallback
        _fallback_store_file(filename, content)
        trace = traceback.format_exc(limit=6)
        logger.error(f"Erro upload KB '{filename}' (usando fallback): {e}")
        files = _merged_kb_filenames(p)
        html_list = render_template('_lista_kb.html', kb_files=files)
        err = f"<div class='alert alert-danger p-2 mb-2'>Erro ao indexar (usado fallback): {e}<details class='small'><summary>Detalhes</summary><pre class='mb-0'>{trace}</pre></details></div>"
        return err + html_list, 200

@kb_bp.route('/ui/upload_test', methods=['POST'])
@login_required
def kb_upload_test():
    f = request.files.get('file')
    if not f:
        return {"status":"erro","detalhe":"sem arquivo"}, 400
    return {"status":"ok","filename":f.filename,"size":len(f.read())}

@kb_bp.route('/ui/delete/<path:filename>', methods=['DELETE'])
@login_required
def kb_delete(filename):
    # Decodificar URL encoding
    filename = unquote(filename)
    
    try:
        p = _get_kb_pipeline()
        
        # Deletar do Chroma vector store
        removed = p.delete_from_global_kb_by_filename(filename)
        
        # Deletar do fallback também (se existir)
        fallback_names = _load_fallback_index()
        if filename in fallback_names:
            fallback_names.remove(filename)
            _save_fallback_index(fallback_names)
            
            # Tentar remover arquivo físico do fallback
            safe_name = filename.replace('/', '_')
            fallback_file = FALLBACK_KB_DIR / safe_name
            if fallback_file.exists():
                try:
                    fallback_file.unlink()
                    logger.info(f"Arquivo fallback removido: {safe_name}")
                except Exception as e:
                    logger.warning(f"Falha ao remover arquivo fallback {safe_name}: {e}")
        
        # Obter lista atualizada
        files = _merged_kb_filenames(p)
        
        # Calcular estatísticas atualizadas
        kb_stats = {'total': len(files), 'pdf': 0, 'image': 0, 'audio': 0, 'video': 0, 'text': 0}
        for f in files:
            ext = f.split('.')[-1].lower() if '.' in f else ''
            if ext == 'pdf':
                kb_stats['pdf'] += 1
            elif ext == 'txt':
                kb_stats['text'] += 1
            elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                kb_stats['image'] += 1
            elif ext in ['mp3', 'wav']:
                kb_stats['audio'] += 1
            elif ext in ['mp4', 'mov']:
                kb_stats['video'] += 1
        
        html_list = render_template('_lista_kb.html', kb_files=files)
        
        if removed or filename in fallback_names:
            logger.info(f"Arquivo '{filename}' removido da KB (Chroma: {removed} chunks)")
            return html_list
        else:
            logger.warning(f"Tentativa de remover arquivo não encontrado: '{filename}'")
            return "<div class='alert alert-warning p-2'>Arquivo não encontrado na KB.</div>" + html_list, 404
    
    except Exception as e:
        logger.error(f"Erro ao deletar arquivo '{filename}': {e}", exc_info=True)
        return f"<div class='alert alert-danger p-2'>Erro ao remover: {e}</div>", 500
