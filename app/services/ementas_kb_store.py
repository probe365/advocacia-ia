# app/services/ementas_kb_store.py
from __future__ import annotations
import os, json, threading
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

class EmentasFAISSStore:
    """
    Armazena embeddings em FAISS + metadados em JSONL lado a lado.
    Persistência em disco: <base_dir>/index.faiss, meta.jsonl, ids.npy
    """
    def __init__(self, base_dir: str, model_name: str = DEFAULT_MODEL):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        self.model = SentenceTransformer(model_name)   # CPU ok
        self.dim = self.model.get_sentence_embedding_dimension()

        self.index_path = os.path.join(self.base_dir, "index.faiss")
        self.meta_path  = os.path.join(self.base_dir, "meta.jsonl")
        self.ids_path   = os.path.join(self.base_dir, "ids.npy")

        self._lock = threading.RLock()

        self.index = None
        self.ids: List[str] = []
        self._load()

    # ---------- persistência ----------
    def _load(self):
        with self._lock:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
            else:
                # Similaridade por cosseno => normalizamos e usamos inner-product
                self.index = faiss.IndexFlatIP(self.dim)

            if os.path.exists(self.ids_path):
                self.ids = list(np.load(self.ids_path, allow_pickle=True))
            else:
                self.ids = []

    def _save(self):
        with self._lock:
            faiss.write_index(self.index, self.index_path)
            np.save(self.ids_path, np.array(self.ids, dtype=object))

    # ---------- util ----------
    def _embed(self, texts: List[str]) -> np.ndarray:
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
        return embs.astype("float32")

    # ---------- APIs públicas ----------
    def upsert_docs(self, docs: List[Dict[str, Any]]) -> int:
        """
        docs: [{"id": "str", "title": "...", "text": "...", "metadados": {...}}]
        """
        if not docs:
            return 0

        texts = [d.get("text", "") or "" for d in docs]
        embs  = self._embed(texts)

        with self._lock:
            # estrategia simples: ids únicos; se já existir, ignoramos (poderia implementar delete+add)
            existing = set(self.ids)
            new_pairs: List[Tuple[str, Dict[str,Any]]] = []
            add_rows = []
            for i, d in enumerate(docs):
                doc_id = str(d.get("id") or f"auto:{len(self.ids)+i}")
                if doc_id in existing:
                    continue
                new_pairs.append((doc_id, d))
                add_rows.append(i)

            if not add_rows:
                return 0

            add_vecs = embs[add_rows]
            self.index.add(add_vecs)

            # salvar metadados
            with open(self.meta_path, "a", encoding="utf-8") as f:
                for doc_id, d in new_pairs:
                    f.write(json.dumps({"id": doc_id, **d}, ensure_ascii=False) + "\n")
                    self.ids.append(doc_id)

            self._save()
            return len(add_rows)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        q = query.strip()
        if not q:
            return []

        qv = self._embed([q])  # (1, dim)
        with self._lock:
            if self.index.ntotal == 0:
                return []
            scores, idxs = self.index.search(qv, top_k)  # inner product ~ cos sim (normalizados)
            idxs = idxs[0].tolist()
            scores = scores[0].tolist()

        # recuperar metadados pelo deslocamento (ordem de inserção)
        # como gravamos linha a linha, vamos mapear rapidamente:
        results = []
        # carregamento leve: lemos o arquivo inteiro uma vez em memória (ok para ~centenas de milhares)
        metas = []
        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                metas.append(json.loads(line))

        for rank, (i, s) in enumerate(zip(idxs, scores)):
            if i < 0 or i >= len(metas):
                continue
            m = metas[i]
            results.append({
                "rank": rank+1,
                "score": float(s),
                "id": m.get("id"),
                "title": m.get("title"),
                "text": m.get("text"),
                "metadados": m.get("metadados", {}),
            })
        return results

