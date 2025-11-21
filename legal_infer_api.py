# -*- coding: utf-8 -*-
"""
Flask inference API for 'Advocacia e IA'
- Loads Word2Vec + BiLSTMClassifier artifacts trained previously
- Exposes /predict and /similar endpoints
- Provides a lightweight semantic index (pickle) based on W2V mean embeddings

Run (Windows / PowerShell):
python legal_infer_api.py --models-dir "models\legal_bilstm_v5b" --host 0.0.0.0 --port 8000
"""

import os
import io
import json
import argparse
import threading
import pickle
from typing import List, Dict, Any, Tuple

import numpy as np
from flask import Flask, request, jsonify
# Optional flask_cors: import only if the package is available to avoid lint/import errors
try:
    import importlib.util
    if importlib.util.find_spec("flask_cors") is not None:
        import importlib
        _mod = importlib.import_module("flask_cors")
        CORS = getattr(_mod, "CORS", None)
        _HAS_CORS = CORS is not None
    else:
        CORS = None
        _HAS_CORS = False
except Exception:
    CORS = None
    _HAS_CORS = False

import torch
import torch.nn as nn
from gensim.models import KeyedVectors


# --------------------------
# Tokenizer & helpers
# --------------------------
PAD_IDX = 0
UNK_IDX = 1

def basic_tokenize_lower_ws(text: str) -> List[str]:
    return str(text).lower().split()

def text_to_ids(text: str, vocab: Dict[str, int], max_len: int) -> np.ndarray:
    toks = basic_tokenize_lower_ws(text)
    ids = [vocab.get(t, UNK_IDX) for t in toks[:max_len]]
    if len(ids) < max_len:
        ids += [PAD_IDX] * (max_len - len(ids))
    return np.array(ids, dtype=np.int64)

def batchify_texts(texts: List[str], vocab: Dict[str, int], max_len: int) -> torch.Tensor:
    arr = np.stack([text_to_ids(t, vocab, max_len) for t in texts], axis=0)
    return torch.tensor(arr, dtype=torch.long)


# --------------------------
# Model definition (must mirror training)
# --------------------------
class BiLSTMClassifier(nn.Module):
    def __init__(self,
                 vocab_size: int,
                 embed_dim: int,
                 hidden_dim: int,
                 num_classes: int,
                 pad_idx: int,
                 w2v_weights: np.ndarray,
                 freeze_embeddings: bool = True,
                 num_layers: int = 1,
                 dropout: float = 0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        with torch.no_grad():
            self.embedding.weight.copy_(torch.tensor(w2v_weights, dtype=torch.float))
        self.embedding.weight.requires_grad = not freeze_embeddings

        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x):
        emb = self.embedding(x)              # (B, L, E)
        out, _ = self.lstm(emb)              # (B, L, 2H)
        # Pooling: mean over time (you used something equivalent during training)
        pooled = out.mean(dim=1)             # (B, 2H)
        logits = self.fc(self.dropout(pooled))
        return logits


# --------------------------
# Semantic search using W2V mean
# --------------------------
def sent_w2v_mean(text: str, kv: KeyedVectors, dim: int) -> np.ndarray:
    toks = basic_tokenize_lower_ws(text)
    vecs = []
    for t in toks:
        if t in kv:
            vecs.append(kv[t])
    if not vecs:
        return np.zeros(dim, dtype=np.float32)
    v = np.vstack(vecs).mean(axis=0)
    # L2 normalize for cosine
    n = np.linalg.norm(v) + 1e-12
    return (v / n).astype(np.float32)

def cosine_sim_matrix(q: np.ndarray, M: np.ndarray) -> np.ndarray:
    # q: (D,) normalized; M: (N, D) normalized
    return (M @ q)


# --------------------------
# Flask App
# --------------------------
def create_app(models_dir: str) -> Flask:
    app = Flask(__name__)
    if _HAS_CORS:
        CORS(app)

    # ==== Load artifacts ====
    cfg_path = os.path.join(models_dir, "config.json")
    vocab_path = os.path.join(models_dir, "vocab.pkl")
    le_path = os.path.join(models_dir, "label_encoder.pkl")
    best_model_path = os.path.join(models_dir, "best_model.pt")
    model_path = os.path.join(models_dir, "model.pt")
    kv_path = os.path.join(models_dir, "w2v.kv")
    index_path = os.path.join(models_dir, "semantic_index.pkl")

    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Missing config.json in {models_dir}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    with open(vocab_path, "rb") as f:
        vocab = pickle.load(f)
    with open(le_path, "rb") as f:
        le = pickle.load(f)

    # Word2Vec
    kv = KeyedVectors.load(kv_path, mmap='r')
    embed_dim = int(cfg.get("embed_dim", kv.vector_size))
    if embed_dim != kv.vector_size:
        raise ValueError(f"Embedding dim mismatch: cfg={embed_dim} vs kv={kv.vector_size}")

    # Build embedding matrix aligned with vocab indices
    vocab_size = len(vocab)
    w2v_weights = np.random.normal(scale=0.01, size=(vocab_size, embed_dim)).astype(np.float32)
    w2v_weights[PAD_IDX] = 0.0  # PAD is zero vector
    for tok, idx in vocab.items():
        if tok in kv:
            w2v_weights[idx] = kv[tok]

    # Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = BiLSTMClassifier(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        hidden_dim=int(cfg.get("hidden_dim", 128)),
        num_classes=len(le.classes_),
        pad_idx=PAD_IDX,
        w2v_weights=w2v_weights,
        freeze_embeddings=bool(cfg.get("freeze_embeddings_at_infer", True)),
        num_layers=int(cfg.get("num_layers", 1)),
        dropout=float(cfg.get("dropout", 0.1))
    ).to(device)
    state_path = best_model_path if os.path.exists(best_model_path) else model_path
    model.load_state_dict(torch.load(state_path, map_location=device))
    model.eval()

    max_len = int(cfg.get("max_len", 256))

    # ==== Semantic Index (id, text, vec) ====
    _index_lock = threading.Lock()
    if os.path.exists(index_path):
        with open(index_path, "rb") as f:
            index_store = pickle.load(f)
    else:
        index_store = {"items": [], "mat": None}  # mat: (N, D) normalized float32

    def _rebuild_matrix():
        if not index_store["items"]:
            index_store["mat"] = None
            return
        M = np.vstack([it["vec"] for it in index_store["items"]]).astype(np.float32)
        # Ensure normalized
        n = np.linalg.norm(M, axis=1, keepdims=True) + 1e-12
        M = M / n
        index_store["mat"] = M

    # Ensure matrix in memory
    _rebuild_matrix()

    # ------------- Routes -------------
    @app.get("/health")
    def health():
        payload = {
            "ok": True,
            "device": str(device),
            "classes": len(le.classes_),
            "vocab_size": len(vocab),
            "embed_dim": embed_dim,
            "indexed_docs": len(index_store["items"])
        }
        return jsonify(payload)

    @app.post("/predict")
    def predict():
        data = request.get_json(force=True)
        text = data.get("text", "")
        if not text.strip():
            return jsonify({"error": "Empty 'text'"}), 400
        xb = batchify_texts([text], vocab, max_len).to(device)
        with torch.no_grad():
            logits = model(xb)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pred_idx = int(probs.argmax())
        return jsonify({
            "label": le.classes_[pred_idx],
            "index": pred_idx,
            "confidence": float(probs[pred_idx])
        })

    @app.post("/batch_predict")
    def batch_predict():
        data = request.get_json(force=True)
        texts = data.get("texts", [])
        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({"error": "Provide a non-empty 'texts' list"}), 400
        xb = batchify_texts(texts, vocab, max_len).to(device)
        with torch.no_grad():
            logits = model(xb)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        results = []
        for p in probs:
            idx = int(p.argmax())
            results.append({
                "label": le.classes_[idx],
                "index": idx,
                "confidence": float(p[idx])
            })
        return jsonify(results)

    @app.post("/index")
    def index_docs():
        """
        Body:
        {
          "docs": [
            {"id":"E0001","text":"EMENTA: ..."},
            {"id":"E0002","text":"..."}
          ]
        }
        """
        data = request.get_json(force=True)
        docs = data.get("docs", [])
        if not isinstance(docs, list) or len(docs) == 0:
            return jsonify({"error": "Provide 'docs' as a non-empty list"}), 400

        added, updated = 0, 0
        with _index_lock:
            id2pos = {it["id"]: i for i, it in enumerate(index_store["items"])}
            for d in docs:
                did = str(d.get("id", "")).strip()
                txt = str(d.get("text", "")).strip()
                if not did or not txt:
                    continue
                vec = sent_w2v_mean(txt, kv, embed_dim)  # already normalized
                item = {"id": did, "text": txt, "vec": vec}
                if did in id2pos:
                    index_store["items"][id2pos[did]] = item
                    updated += 1
                else:
                    index_store["items"].append(item)
                    added += 1
            _rebuild_matrix()
            # persist
            with open(index_path, "wb") as f:
                pickle.dump(index_store, f)
        return jsonify({"added": added, "updated": updated, "total": len(index_store["items"])})

    @app.post("/similar")
    def similar():
        """
        Body:
        {
          "query": "texto da sua tese...",
          "k": 10
        }
        """
        data = request.get_json(force=True)
        query = data.get("query", "")
        k = int(data.get("k", 10))
        if not query.strip():
            return jsonify({"error": "Empty 'query'"}), 400

        with _index_lock:
            M = index_store["mat"]
            items = index_store["items"]
            if M is None or len(items) == 0:
                return jsonify({"error": "Index is empty. POST /index first."}), 400

        q = sent_w2v_mean(query, kv, embed_dim)  # normalized
        sims = cosine_sim_matrix(q, M)           # (N,)
        topk = np.argsort(-sims)[:max(1, k)]
        results = []
        for i in topk:
            it = items[int(i)]
            results.append({
                "id": it["id"],
                "similarity": float(sims[i]),
                "snippet": it["text"][:300]
            })
        return jsonify(results)

    @app.post("/reset_index")
    def reset_index():
        with _index_lock:
            index_store["items"] = []
            index_store["mat"] = None
            if os.path.exists(index_path):
                os.remove(index_path)
        return jsonify({"ok": True})

    return app


# --------------------------
# Main
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-dir", required=True, help="Folder with best_model.pt, w2v.kv, vocab.pkl, label_encoder.pkl, config.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app = create_app(args.models_dir)
    # threaded=True keeps it simple for local dev; for prod, run via gunicorn/uwsgi
    app.run(host=args.host, port=args.port, threaded=True)

if __name__ == "__main__":
    main()
