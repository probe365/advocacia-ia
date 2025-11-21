# app/blueprints/ementas_faiss.py
from flask import Blueprint, request, render_template, jsonify, current_app
from flask_login import login_required
from pathlib import Path
import numpy as np
import pickle
import faiss
import glob
import os

faiss_bp = Blueprint("ementas_faiss", __name__, url_prefix="/ementas/faiss")

# Caminhos do índice
INDEX_PATH = Path("data/store/ementas_faiss/index.faiss")
META_PATH  = Path("data/store/ementas_faiss/metadados.pkl")

# Singletons em memória
_model = None
_index = None
_meta  = None


# --------------------------
# Utilidades de modelo/index
# --------------------------
def _ensure_model():
    """Carrega modelo de embeddings (mesma dimensão do índice: 384)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Mantive o MiniLM-L6-v2 (384d). Se você indexou com outro, alinhe aqui.
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _ensure_faiss():
    """Carrega índice FAISS e metadados."""
    global _index, _meta
    if _index is None or _meta is None:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError(
                f"Índice ou metadados ausentes.\nINDEX_PATH={INDEX_PATH}\nMETA_PATH={META_PATH}"
            )
        _index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            _meta = pickle.load(f)
    return _index, _meta


# --------------------------
# Resumo do Caso (para FAISS)
# --------------------------
def _read_text_if_exists(p: Path) -> str:
    try:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return ""

def get_resumo_do_caso(case_id: str) -> str:
    """
    Tenta ler o resumo do caso em vários locais conhecidos.
    Aceita tanto "caso_8d9e73b3" quanto "8d9e73b3" como input.
    Ordem:
      1) data/cases/<id>/resumo.txt
      2) cases/<id>/resumo.txt
      3) data/cases/<id>/cache/summary_*.txt (pega o mais recente)
      4) cases/<id>/cache/summary_*.txt (pega o mais recente)
    """
    if not case_id:
        return ""
    
    # Normalizar o case_id - aceitar tanto "8d9e73b3" quanto "caso_8d9e73b3"
    if not case_id.startswith("caso_"):
        case_id = f"caso_{case_id}"

    # 1/2) caminhos diretos
    candidates = [
        Path(f"data/cases/{case_id}/resumo.txt"),
        Path(f"cases/{case_id}/resumo.txt"),
    ]
    for c in candidates:
        txt = _read_text_if_exists(c)
        if txt:
            return txt

    # 3/4) cache (pega o arquivo de summary mais recente)
    for base in (Path(f"data/cases/{case_id}/cache"), Path(f"cases/{case_id}/cache")):
        try:
            paths = sorted(glob(str(base / "summary_*.txt")))
            if paths:
                # mais recente por ordem alfabética já costuma refletir data/hash,
                # mas garantimos pela mtime:
                paths_sorted = sorted(paths, key=lambda p: Path(p).stat().st_mtime, reverse=True)
                txt = _read_text_if_exists(Path(paths_sorted[0]))
                if txt:
                    return txt
        except Exception:
            pass
    
    # 5) Fallback: tentar Pipeline.summarize_with_cache se disponível
    try:
        from pipeline import Pipeline
        pipeline = Pipeline(case_id=case_id)
        resumo, _ = pipeline.summarize_with_cache('Resumo geral do caso')
        if resumo and resumo.strip():
            return resumo.strip()
    except Exception:
        pass

    return ""


@faiss_bp.get("/resumo", endpoint="resumo_faiss")
def resumo_faiss():
    case_id = (request.args.get("case_id") or "").strip()
    if not case_id:
        return jsonify(ok=False, error="case_id ausente"), 400
    
    # Log para debug
    original_case_id = case_id
    if not case_id.startswith("caso_"):
        case_id = f"caso_{case_id}"
    
    resumo = get_resumo_do_caso(case_id)
    if not resumo:
        # Verificar se a pasta do caso existe
        import os
        case_paths = [f"cases/{case_id}", f"data/cases/{case_id}"]
        existing_paths = [p for p in case_paths if os.path.exists(p)]
        
        error_msg = f"Resumo não encontrado para '{original_case_id}' (normalizado: '{case_id}')"
        if existing_paths:
            error_msg += f". Pasta encontrada: {existing_paths[0]}"
        else:
            error_msg += f". Pastas verificadas: {case_paths}"
        
        return jsonify(ok=False, error=error_msg), 404
    
    return jsonify(ok=True, resumo=resumo), 200


# --------------------------
# Diagnóstico
# --------------------------
@faiss_bp.get("/ping")
def ping():
    try:
        _ensure_model()
        _, meta = _ensure_faiss()
        # opcional: verificar dimensão via vetor dummy
        return jsonify(ok=True, meta=len(meta)), 200
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


# --------------------------
# Núcleo de busca (para UI)
# --------------------------
def _search_cards(query: str, top_k: int = 5):
    """
    Executa a busca no FAISS e formata itens para o template _faiss_cards.html.
    - título: do metadado
    - excerto: 'text' minúsculo, truncado
    - fonte: montagem leve (source / orgao / grupo / data_decisao)
    """
    model = _ensure_model()
    index, metadata = _ensure_faiss()

    emb = model.encode([query], normalize_embeddings=True)
    D, I = index.search(np.asarray(emb, dtype="float32"), top_k)

    items = []
    for rank, (dist, idx) in enumerate(zip(D[0], I[0]), start=1):
        if idx < 0 or idx >= len(metadata):
            continue

        m = metadata[idx] or {}

        titulo = (m.get("title") or "").strip() or "—"
        texto_original = (m.get("text") or "").strip()  # Keep original text for export
        texto_lower = texto_original.lower()  # Lowercase version for display excerpt
        exc = texto_lower.replace("\n", " ").strip()
        if len(exc) > 700:
            exc = exc[:700] + "…"

        # linha "Fonte: ..."
        fonte_bits = []
        if m.get("source"):
            fonte_bits.append(m["source"])
        if m.get("orgao"):
            fonte_bits.append(m["orgao"])
        if m.get("grupo"):
            fonte_bits.append(m["grupo"])
        if m.get("data_decisao"):
            fonte_bits.append(str(m["data_decisao"]))
        fonte = ", ".join(fonte_bits) if fonte_bits else "ementa_kb_upload"

        items.append({
            "rank":   rank,
            "score":  float(dist),
            "titulo": titulo,
            "excerto": exc,
            "fonte":  fonte,
            "id":     m.get("id", ""),
            # Full original text (preserving case and formatting) for export/copy
            "texto_full": texto_original,
        })

    return items


# --------------------------
# Rota que devolve HTML (cartões) para HTMX/Fetch
# --------------------------
@faiss_bp.post("/ui/buscar")
def ui_buscar():
    """
    Aceita form (application/x-www-form-urlencoded) ou JSON.
    Campos: q (query), k (top_k)
    Retorna fragmento HTML com cartões, no formato do painel clássico.
    """
    data  = request.form or request.get_json(silent=True) or {}
    query = (data.get("q") or data.get("query") or "").strip()
    try:
        top_k = int(data.get("k") or data.get("top_k") or 10)
    except Exception:
        top_k = 10
    top_k = max(1, min(50, top_k))

    if not query:
        return render_template("_faiss_cards.html", items=[], warn="Digite um texto para consulta."), 200

    try:
        items = _search_cards(query, top_k)
        return render_template("_faiss_cards.html", items=items, warn=None), 200
    except Exception as e:
        current_app.logger.exception("Falha na busca FAISS")
        return render_template("_faiss_cards.html", items=[], warn=f"Erro: {e}"), 200


# --------------------------
# Export functionality
# --------------------------
@faiss_bp.route('/ui/export_txt', methods=['POST'])
@login_required
def export_faiss_txt():
    """Export individual FAISS ementa as downloadable .TXT file"""
    from flask import make_response
    import re
    from datetime import datetime
    
    texto = request.form.get('texto', '').strip()
    titulo = request.form.get('titulo', 'ementa').strip()
    fonte = request.form.get('fonte', '').strip()
    score = request.form.get('score', '').strip()
    
    if not texto:
        return "Texto vazio", 400
    
    # Build formatted content
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    header = f"""EMENTA - EXPORTAÇÃO FAISS
Data: {timestamp}
Título: {titulo}
Fonte: {fonte}
Similaridade: {score}

{'='*60}

"""
    
    full_content = header + texto
    
    # Create safe filename
    safe_titulo = re.sub(r'[^\w\-_\.]', '_', titulo[:50])
    if not safe_titulo:
        safe_titulo = "ementa_faiss"
    filename = f"{safe_titulo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Create response
    response = make_response(full_content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Length'] = len(full_content.encode('utf-8'))
    
    return response


@faiss_bp.route('/ui/export_all_txt', methods=['POST'])
@login_required
def export_all_faiss_txt():
    """Export all FAISS search results as a single .TXT file"""
    from flask import make_response
    import re
    from datetime import datetime
    
    query = request.form.get('query', '').strip()
    k = int(request.form.get('k', 10))
    
    if not query:
        return "Query vazia", 400
    
    try:
        # Get search results
        items = _search_cards(query, k)
        
        if not items:
            return "Nenhum resultado encontrado", 404
        
        # Build consolidated content
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        header = f"""EMENTAS FAISS - EXPORTAÇÃO COMPLETA
Data: {timestamp}
Consulta: {query}
Total de resultados: {len(items)}

{'='*80}

"""
        
        content_parts = [header]
        
        for i, item in enumerate(items, 1):
            # Handle both dict and object access patterns
            if isinstance(item, dict):
                titulo = item.get('titulo', f'Ementa {i}')
                fonte = item.get('fonte', 'N/A')
                score = item.get('score', 0.0)
                texto = item.get('texto_full', '') or item.get('excerto', '')
                item_id = item.get('id', f'item_{i}')
            else:
                titulo = getattr(item, 'titulo', f'Ementa {i}')
                fonte = getattr(item, 'fonte', 'N/A')
                score = getattr(item, 'score', 0.0)
                texto = getattr(item, 'texto_full', '') or getattr(item, 'excerto', '')
                item_id = getattr(item, 'id', f'item_{i}')
            
            section = f"""[{i:02d}] {titulo}
ID: {item_id}
Fonte: {fonte}
Similaridade: {score:.4f}
Conteúdo:
{'-'*40}
{texto}

{'='*80}

"""
            content_parts.append(section)
        
        full_content = "".join(content_parts)
        
        # Create safe filename
        safe_query = re.sub(r'[^\w\-_\.]', '_', query[:30])
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ementas_faiss_{safe_query}_{timestamp_str}.txt"
        
        # Create response
        response = make_response(full_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Length'] = len(full_content.encode('utf-8'))
        
        return response
        
    except Exception as e:
        return f"Erro ao exportar: {str(e)}", 500
