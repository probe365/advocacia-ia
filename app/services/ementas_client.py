# app/services/ementas_client.py
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class EmentasSearchClient:
    """
    Tiny client: carrega um SentenceTransformer, um índice FAISS e
    mantém um mapeamento id->metadata. Guarda tudo em disco.
    """
    def __init__(self,
                 model_name: str,
                 index_path: Path,
                 store_path: Path,
                 normalize: bool = True):
        self.model = SentenceTransformer(model_name)
        self.index_path = Path(index_path)
        self.store_path = Path(store_path)
        self.normalize = normalize

        self.index = None  # faiss.Index
        self.meta: Dict[int, Dict[str, Any]] = {}

        self._load_or_init()

    def _load_or_init(self):
        self.store_path.mkdir(parents=True, exist_ok=True)
        meta_fp = self.store_path / "meta.npy"

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            if meta_fp.exists():
                # dtype=object para dicionários
                self.meta = {int(k): v.item() for k, v in np.load(meta_fp, allow_pickle=True)}
        else:
            # Começa vazio (usar índice flat L2; troque p/ IVFFlat/HNSW depois)
            self.index = faiss.IndexFlatIP(768)  # 768 para MiniLM; ajuste conforme o modelo
            self._persist()

    def _persist(self):
        faiss.write_index(self.index, str(self.index_path))
        # salva meta como pares (idx -> dict)
        items = np.array(list(self.meta.items()), dtype=object)
        np.save(self.store_path / "meta.npy", items, allow_pickle=True)

    def _embed(self, texts: Iterable[str]) -> np.ndarray:
        vecs = self.model.encode(list(texts), convert_to_numpy=True, show_progress_bar=False)
        if self.normalize:
            faiss.normalize_L2(vecs)
        return vecs

    def index_texts(self, docs: List[Dict[str, Any]]) -> int:
        """
        docs: [{"text": "...", "label": "...", "id": "...", "title": "...", ...}, ...]
        Retorna quantos foram indexados.
        """
        if not docs:
            return 0
        texts = [d["text"] for d in docs]
        vecs = self._embed(texts)

        start_id = self.index.ntotal
        self.index.add(vecs)

        for i, d in enumerate(docs):
            self.meta[start_id + i] = d

        self._persist()
        return len(docs)

    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        qv = self._embed([query])
        scores, ids = self.index.search(qv, k)
        out = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            item = dict(self.meta.get(int(idx), {}))
            item["_score"] = float(score)
            out.append(item)
        return out
