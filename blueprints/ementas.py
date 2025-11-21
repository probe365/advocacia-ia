# app/blueprints/ementas.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from pathlib import Path
import numpy as np
import pickle, faiss

ementas_faiss = Blueprint("ementas_faiss", __name__, url_prefix="/ementas/faiss")

# Caminhos
INDEX_PATH = Path("data/store/ementas_faiss/index.faiss")
META_PATH  = Path("data/store/ementas_faiss/metadados.pkl")

# Use o MESMO modelo da indexação
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None
_index = None
_metadata = None
_dim = None

def _ensure_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def _ensure_faiss():
    """Carrega índice e metadados; detecta dimensão do índice."""
    global _index, _metadata, _dim
    if _index is None or _metadata is None:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError(f"Índice/Meta não encontrados:\n{INDEX_PATH}\n{META_PATH}")
        _index = faiss.read_index(str(INDEX_PATH))
        _dim = _index.d  # dimensão do vetor
        with open(META_PATH, "rb") as f:
            _metadata = pickle.load(f)
    return _index, _metadata, _dim

def _first_non_empty(md: dict, *keys, default=""):
    """Pega o primeiro valor não-vazio dado um conjunto de chaves alternativas."""
    for k in keys:
        v = md.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return default

def _make_preview(text: str, limit=380):
    t = (text or "").replace("\r", " ").replace("\n", " ").strip()
    return (t[:limit] + "…") if len(t) > limit else t

@ementas_faiss.route("/ping", methods=["GET"])
def ping():
    try:
        _ensure_model()
        _, meta, dim = _ensure_faiss()
        return jsonify(ok=True, dim=dim, meta=len(meta))
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

# -------- ROTA PRINCIPAL USADA PELO WIDGET --------
@ementas_faiss.route("/buscar", methods=["POST"])
# @login_required  # se quiser exigir login, descomente (o widget envia cookies)
def buscar():
    """
    Body JSON: { "query": "...", "top_k": 10 }
    Retorna: { ok: true, results: [ {rank,id,title,ementa,ementa_full,score,orgao,grupo,data_decisao,source,path} ] }
    """
    try:
        data  = request.get_json(force=True) or {}
        query = (data.get("query") or "").strip()
        top_k = max(1, min(50, int(data.get("top_k") or 10)))

        if not query:
            return jsonify(ok=False, error="query vazio"), 400

        model = _ensure_model()
        index, metadata, _ = _ensure_faiss()

        # encode consulta (normalizada para IP ~ cosseno)
        emb = model.encode([query], normalize_embeddings=True).astype("float32")
        D, I = index.search(emb, top_k)  # D: similaridade (se IndexFlatIP), I: índices

        results = []
        for rank, (dist, idx) in enumerate(zip(D[0], I[0]), start=1):
            if idx < 0 or idx >= len(metadata):
                continue
            m = metadata[idx] or {}

            # Mapeamentos de fallback
            _id     = _first_non_empty(m, "id", "id_decisao", "doc_id", "pk", default="")
            _title  = _first_non_empty(m, "title", "titulo", "label", "rotulo", default="")
            # Texto integral pode ter vários nomes:
            full    = _first_non_empty(m, "ementa", "text", "texto", "conteudo", default="")
            trecho  = _make_preview(full)  # preview curto

            orgao   = _first_non_empty(m, "orgao", "órgão", "orgão", "org", default="")
            grupo   = _first_non_empty(m, "grupo", "secao", "seção", "turma", default="")
            data    = _first_non_empty(m, "data_decisao", "data", "data_julgamento", default="")
            source  = _first_non_empty(m, "source", "fonte", default="")
            path    = _first_non_empty(m, "path", "arquivo", default="")

            # Se quiser converter distância/similaridade:
            score = float(dist)  # já vem em [-1..1] p/ IP (por ser normalizado); mostramos como veio

            results.append({
                "rank": rank,
                "id": _id,
                "title": _title,
                "ementa": trecho,
                "ementa_full": full,
                "score": round(score, 4),
                "orgao": orgao,
                "grupo": grupo,
                "data_decisao": data,
                "source": source,
                "path": path
            })

        return jsonify(ok=True, results=results)

    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500
