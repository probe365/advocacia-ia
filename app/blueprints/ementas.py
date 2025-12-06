from flask import Blueprint, request, render_template, jsonify
import html
from flask_login import login_required
from pipeline import Pipeline
from werkzeug.utils import secure_filename
import os

# app/blueprints/ementas.py
# duplicate imports removed; the blueprint is defined later in this file so no relative import is needed

from app.services.ementas_kb_store import EmentasFAISSStore

# Base local para o índice
_EMENTAS_DIR = os.environ.get("EMENTAS_STORE_DIR", "data/ementas_faiss")
store = EmentasFAISSStore(_EMENTAS_DIR)

from app.model_server import model_server

ementas_bp = Blueprint('ementas', __name__, url_prefix='/ementas')


# --- Healthcheck simples ---
@ementas_bp.route("/ping", methods=["GET"])
def ementas_ping():
    return jsonify(ok=True)

# --- Endpoint de indexação usado pelo script ---
# NÃO coloque @login_required aqui se o script roda fora do browser.
@ementas_bp.route("/index", methods=["POST"])
def ementas_index():
    payload = request.get_json(force=True, silent=True) or {}
    docs = payload.get("docs", [])
    if not isinstance(docs, list):
        return jsonify(error="field 'docs' must be a list"), 400

    try:
        added = store.upsert_docs(docs)
        return jsonify(indexed=added), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@ementas_bp.route('/ui/painel', methods=['GET'])
@login_required
def painel_ementas():
    p = Pipeline(case_id='kb_dummy')
    arquivos = p.get_indexed_ementa_filenames()
    return render_template('ementas.html', ementa_files=arquivos)


@ementas_bp.route('/ui/classificar', methods=['POST'])
@login_required
def classificar_texto():
    texto = (request.form.get('q') or '').strip()
    if not texto:
        return "<div class='alert alert-warning p-2'>Texto vazio.</div>", 400
    try:
        # chama o modelo
        label, top = model_server.predict(texto)
        # monta HTML leve
        lis = "".join([f"<li class='list-group-item d-flex justify-content-between'><span>{html.escape(lbl)}</span><span class='badge bg-secondary'>{prob:.3f}</span></li>" for lbl, prob in top])
        html_out = f"""
        <div class='card mb-2'>
          <div class='card-header py-2'>Classe prevista</div>
          <div class='card-body py-2'>
            <div class='d-flex justify-content-between align-items-center mb-2'>
              <div><span class='badge bg-primary'>{html.escape(label)}</span></div>
              <button class='btn btn-sm btn-outline-secondary' id='btn-usar-classe'>Usar na busca</button>
            </div>
            <ul class='list-group list-group-flush'>{lis}</ul>
          </div>
        </div>
        <script>
        document.getElementById('btn-usar-classe').onclick = () => {{
          const tag = "{label}";
          const box = document.getElementById('ementa-query-box');
          if (box) {{
            box.value = (box.value || "") + "\\n\\n[FiltroClasse:{label}]";
          }}
          alert("Filtro sugerido adicionado ao texto da consulta.");
        }};
        </script>
        """
        return html_out
    except Exception as e:
        return f"<div class='alert alert-danger p-2'>Falha na classificação: {e}</div>", 500


@ementas_bp.route('/ui/upload', methods=['POST'])
@login_required
def upload_ementas():
    p = Pipeline(case_id='kb_dummy')
    files = request.files.getlist('files') or []
    if not files:
        return "<div class='alert alert-warning p-2'>Nenhum arquivo enviado.</div>", 400
    docs = []
    for f in files:
        filename = secure_filename(f.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.pdf', '.txt']:
            continue
        content_bytes = f.read()
        try:
            if ext == '.pdf':
                # Usa ingestion existente apenas para extrair texto
                txt = p.ingestion_handler.extract_text_from_pdf_bytes(content_bytes) or ''
            else:
                txt = content_bytes.decode('utf-8', errors='ignore')
            if txt.strip():
                docs.append({'filename': filename, 'content': txt})
        except Exception:
            continue
    added = p.ingest_ementas_to_kb(docs) if docs else 0
    lista = p.get_indexed_ementa_filenames()
    html_list = render_template('_lista_ementas.html', ementa_files=lista)
    msg = f"<div class='alert alert-success p-2 mb-2'>{added} arquivo(s) indexado(s).</div>" if added else "<div class='alert alert-warning p-2 mb-2'>Nenhum arquivo válido processado.</div>"
    return msg + html_list

@ementas_bp.route("/search", methods=["POST"])
def ementas_search():
    payload = request.get_json(force=True, silent=True) or {}
    query = payload.get("query", "")
    k = int(payload.get("k", 10))
    try:
        hits = store.search(query, top_k=k)
        return jsonify(results=hits), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@ementas_bp.route('/ui/resumo/<case_id>', methods=['GET'])
@login_required
def obter_resumo_case(case_id: str):
    """Retorna um resumo breve do caso para pré-preencher a busca (limite defensivo)."""
    try:
        pipeline = Pipeline(case_id=case_id)
        resumo, _ = pipeline.summarize_with_cache('Resumo geral do caso')
        resumo = resumo[:5000]  # limite para não inundar textarea
        return f"<textarea class='form-control form-control-sm mb-2' name='q' id='ementa-query-box' rows='6'>{resumo}</textarea>"
    except Exception as e:
        return f"<div class='alert alert-danger p-2'>Erro obtendo resumo: {e}</div>", 500

@ementas_bp.route('/ui/buscar', methods=['POST'])
@login_required
def buscar_ementas():
    mode = request.form.get('mode','manual')
    case_id = (request.form.get('case_id') or '').strip()
    k = int(request.form.get('k') or 5)
    texto_query = (request.form.get('q') or '').strip()
    # Se modo resumo e texto vazio mas case_id fornecido, tentar gerar.
    if mode == 'resumo' and (not texto_query) and case_id:
        try:
            pipeline_case = Pipeline(case_id=case_id)
            texto_query, _ = pipeline_case.summarize_with_cache('Resumo geral do caso')
            texto_query = (texto_query or '').strip()[:8000]
        except Exception:
            pass
    if not texto_query:
        return "<div class='alert alert-warning p-2'>Consulta vazia.</div>", 400
    p = Pipeline(case_id='kb_dummy')
    pairs = p.find_similar_ementas_with_scores(texto_query, top_k=k)
    if not pairs:
        return "<div class='alert alert-info p-2'>Nenhum resultado.</div>"
    
    out = ["<div class='mb-2 small text-muted'>Consulta usada:&nbsp;<span class='fw-semibold'>" + (texto_query[:300].replace('<','&lt;')) + ("..." if len(texto_query)>300 else "") + "</span></div>"]
    
    # Add bulk export button
    out.append(f"""
    <div class='mb-3 d-flex justify-content-between align-items-center'>
        <span class='text-muted small'>{len(pairs)} resultado(s) encontrado(s)</span>
        <button class='btn btn-sm btn-outline-warning export-all-btn' data-query='{html.escape(texto_query, quote=True)}' data-k='{k}'>
            📁 Baixar Todos (.TXT)
        </button>
    </div>
    """)
    
    out.append("<div class='list-group' id='ementa-result-list'>")
    for doc, score in pairs:
        meta = doc.metadata or {}
        fname = meta.get('filename','?')
        # Converter distância em similaridade intuitiva
        try:
            sim = 1/(1+score)
        except Exception:
            sim = 0.0
        snippet_full = doc.page_content.strip()
        snippet_display = snippet_full[:480].replace('\n',' ') + ('...' if len(snippet_full) > 480 else '')
        safe_copy = html.escape(snippet_full[:10000], quote=True).replace("'", "&#39;")
        
        # Create a safe filename from the original filename
        safe_filename = fname.replace('.pdf', '').replace('.txt', '').replace(' ', '_')[:50]
        
        out.append(
            "<div class='list-group-item position-relative'>"
            f"<div class='d-flex justify-content-between'><strong>{html.escape(fname)}</strong><span class='badge bg-secondary'>sim {sim:.3f}</span></div>"
            f"<div class='small text-muted mb-1'>Fonte: {html.escape(meta.get('source','-') or '-')}</div>"
            f"<div class='mb-2' style='white-space:pre-wrap;font-size:0.8rem;'>{html.escape(snippet_display)}</div>"
            f"<div class='btn-group btn-group-sm' role='group'>"
            f"<button class='btn btn-outline-primary copy-btn' data-text='{safe_copy}'>📋 Copiar</button>"
            f"<button class='btn btn-outline-success export-txt-btn' data-text='{safe_copy}' data-filename='{safe_filename}'>💾 Baixar TXT</button>"
            f"<button class='btn btn-outline-info view-full-btn' data-text='{safe_copy}' data-filename='{html.escape(fname)}'>👁️ Ver Completo</button>"
            f"</div>"
            "</div>"
        )
    out.append("</div>")
    # Script único para copy + download + view + scroll
    out.append("""
<script>
// Copy button functionality
document.querySelectorAll('#ementa-result-list .copy-btn').forEach(btn=>{
  btn.onclick = () => {
    navigator.clipboard.writeText(btn.dataset.text); 
    btn.innerHTML='📋 Copiado'; 
    setTimeout(()=>btn.innerHTML='📋 Copiar', 1800);
  };
});

// Download TXT button functionality
document.querySelectorAll('#ementa-result-list .export-txt-btn').forEach(btn=>{
  btn.onclick = () => {
    const text = btn.dataset.text;
    const filename = btn.dataset.filename || 'ementa';
    
    // Create form and submit for download
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/ementas/ui/export_txt';
    form.style.display = 'none';
    
    const textInput = document.createElement('input');
    textInput.type = 'hidden';
    textInput.name = 'texto';
    textInput.value = text;
    
    const filenameInput = document.createElement('input');
    filenameInput.type = 'hidden';
    filenameInput.name = 'filename';
    filenameInput.value = filename;
    
    form.appendChild(textInput);
    form.appendChild(filenameInput);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    btn.innerHTML='💾 Baixando...';
    setTimeout(()=>btn.innerHTML='💾 Baixar TXT', 2000);
  };
});

// Export all results functionality
document.querySelectorAll('.export-all-btn').forEach(btn=>{
  btn.onclick = () => {
    const query = btn.dataset.query;
    const k = btn.dataset.k;
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/ementas/ui/export_all_txt';
    form.style.display = 'none';
    
    const queryInput = document.createElement('input');
    queryInput.type = 'hidden';
    queryInput.name = 'query';
    queryInput.value = query;
    
    const kInput = document.createElement('input');
    kInput.type = 'hidden';
    kInput.name = 'k';
    kInput.value = k;
    
    form.appendChild(queryInput);
    form.appendChild(kInput);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    btn.innerHTML='📁 Preparando...';
    setTimeout(()=>btn.innerHTML='📁 Baixar Todos (.TXT)', 2500);
  };
});

// View full text in modal
document.querySelectorAll('#ementa-result-list .view-full-btn').forEach(btn=>{
  btn.onclick = () => {
    const text = btn.dataset.text;
    const filename = btn.dataset.filename || 'Ementa';
    
    // Use existing modal or create new one
    let modal = document.getElementById('ementaModal');
    if (!modal) {
      // Create modal if it doesn't exist
      modal = document.createElement('div');
      modal.innerHTML = `
        <div class="modal fade" id="ementaModal" tabindex="-1">
          <div class="modal-dialog modal-xl modal-dialog-scrollable">
            <div class="modal-content bg-dark text-light">
              <div class="modal-header">
                <h5 class="modal-title" id="ementaModalLabel">Ementa</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <pre id="ementaModalBody" class="mb-0" style="white-space: pre-wrap;"></pre>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-outline-light btn-sm" data-bs-dismiss="modal">Fechar</button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal.firstElementChild);
      modal = document.getElementById('ementaModal');
    }
    
    // Update modal content
    document.getElementById('ementaModalLabel').textContent = filename;
    document.getElementById('ementaModalBody').textContent = text;
    
    // Show modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
  };
});

// Scroll to results
document.getElementById('ementa-result-list').scrollIntoView({behavior:'smooth', block:'start'});
</script>
""")
    return "".join(out)

@ementas_bp.route('/ui/delete/<filename>', methods=['DELETE'])
@login_required
def delete_ementa(filename):
    p = Pipeline(case_id='kb_dummy')
    removed = p.delete_ementas_by_filename(filename)
    lista = p.get_indexed_ementa_filenames()
    html_list = render_template('_lista_ementas.html', ementa_files=lista)
    if removed:
        return html_list
    return "<div class='alert alert-danger p-2'>Falha ao remover.</div>", 500


@ementas_bp.route('/ui/export_txt', methods=['POST'])
@login_required
def export_ementa_txt():
    """Export full ementa text as downloadable .TXT file"""
    from flask import make_response
    import re
    from datetime import datetime
    
    texto = request.form.get('texto', '').strip()
    filename = request.form.get('filename', 'ementa').strip()
    
    if not texto:
        return "Texto vazio", 400
    
    # Clean filename for safe download
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    if not safe_filename.endswith('.txt'):
        safe_filename += '.txt'
    
    # Create response with proper headers for download
    response = make_response(texto)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
    response.headers['Content-Length'] = len(texto.encode('utf-8'))
    
    return response


@ementas_bp.route('/ui/export_all_txt', methods=['POST'])
@login_required
def export_all_ementas_txt():
    """Export all search results as a single .TXT file"""
    from flask import make_response
    import re
    from datetime import datetime
    
    query = request.form.get('query', '').strip()
    k = int(request.form.get('k', 5))
    
    if not query:
        return "Query vazia", 400
    
    # Get search results
    p = Pipeline(case_id='kb_dummy')
    pairs = p.find_similar_ementas_with_scores(query, top_k=k)
    
    if not pairs:
        return "Nenhum resultado encontrado", 404
    
    # Build consolidated text
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    header = f"""EMENTAS SIMILARES - EXPORTAÇÃO
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Consulta: {query}
Total de resultados: {len(pairs)}

{'='*80}

"""
    
    content_parts = [header]
    
    for i, (doc, score) in enumerate(pairs, 1):
        meta = doc.metadata or {}
        fname = meta.get('filename', f'documento_{i}')
        source = meta.get('source', 'N/A')
        
        # Convert distance to similarity
        try:
            sim = 1/(1+score)
        except:
            sim = 0.0
        
        section = f"""[{i:02d}] {fname}
Fonte: {source}
Similaridade: {sim:.4f}
Conteúdo:
{'-'*40}
{doc.page_content.strip()}

{'='*80}

"""
        content_parts.append(section)
    
    full_content = "".join(content_parts)
    
    # Create safe filename
    safe_query = re.sub(r'[^\w\-_\.]', '_', query[:30])
    filename = f"ementas_similares_{safe_query}_{timestamp}.txt"
    
    # Create response
    response = make_response(full_content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Length'] = len(full_content.encode('utf-8'))
    
    return response
