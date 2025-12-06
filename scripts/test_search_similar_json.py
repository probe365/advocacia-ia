#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Busca por similaridade no índice FAISS das ementas.

Uso básico:
  python scripts/test_search_similar_json.py ^
    --query "ação de indenização por danos morais em contrato bancário" ^
    --top-k 10

Uso com caminhos explícitos:
  python scripts/test_search_similar_json.py ^
    --query "..." ^
    --top-k 10 ^
    --index "C:\\adv-IA-F\\data\\store\\ementas_faiss\\index.faiss" ^
    --meta  "C:\\adv-IA-F\\data\\store\\ementas_faiss\\metadados.pkl"

Uso apontando para a pasta store (carrega index.faiss + metadados.pkl dali):
  python scripts/test_search_similar_json.py ^
    --query "..." ^
    --top-k 10 ^
    --store "C:\\adv-IA-F\\data\\store\\ementas_faiss"
"""

import argparse
import json
import pickle
from pathlib import Path
from datetime import datetime

import numpy as np
import faiss

# Carrega SentenceTransformer apenas quando necessário (import leve)
from sentence_transformers import SentenceTransformer


def load_store_paths(
    store_dir: Path | None,
    index_path: Path | None = None,
    meta_path: Path | None = None,
) -> tuple[Path, Path]:
    """
    Resolve os caminhos do índice e dos metadados a partir de:
    - store_dir (se fornecido), OU
    - index_path/meta_path explícitos.
    """
    if index_path is None or meta_path is None:
        if store_dir is None:
            raise ValueError("Informe --store OU ambos --index e --meta.")
        index_path = store_dir / "index.faiss"
        meta_path = store_dir / "metadados.pkl"
    if index_path is None or meta_path is None:
        raise ValueError("Não foi possível resolver caminhos do índice/metadados.")
    return index_path, meta_path


def ensure_exists(path: Path, kind: str):
    if not path.exists():
        raise FileNotFoundError(f"{kind} não encontrado: {path}")


def load_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    print("🔹 Carregando modelo de embeddings (SentenceTransformer)...")
    model = SentenceTransformer(model_name)
    return model


def load_index(index_path: Path):
    print(f"🔹 Carregando índice FAISS de: {index_path}")
    index = faiss.read_index(str(index_path))
    return index


def load_metadata(meta_path: Path):
    print(f"🔹 Carregando metadados de: {meta_path}")
    with open(meta_path, "rb") as f:
        metadata = pickle.load(f)
    if not isinstance(metadata, (list, tuple)):
        raise ValueError("Formato de metadados inesperado (espera-se uma lista de dicts).")
    return metadata


def embed_query(model: SentenceTransformer, query: str) -> np.ndarray:
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    # Se o índice foi criado para produto interno (IP) usando vetores normalizados,
    # manteremos a normalização aqui (cosine ~ dot product quando normalizado).
    return q.astype(np.float32)


def search(index, qvec: np.ndarray, top_k: int):
    # Executa a busca; d = distâncias (maior = mais similar quando IP)
    dists, idxs = index.search(qvec, top_k)
    # Retorna arrays 1D
    return dists[0], idxs[0]


def format_console_result(rank: int, score: float, row_meta: dict):
    # Campos “id” e “title” podem existir (depende do esquema usado na indexação).
    rid = row_meta.get("id", row_meta.get("id_decisao", ""))
    ttl = row_meta.get("title", row_meta.get("label", ""))

    print(f"# {rank:<2d} score={score:+.4f}  id={rid}  title={ttl}")
    # Trecho inicial do texto (se existir)
    txt = row_meta.get("excerpt") or row_meta.get("ementa") or row_meta.get("text") or ""
    if isinstance(txt, str) and txt.strip():
        snip = txt.strip().replace("\n", " ")
        if len(snip) > 200:
            snip = snip[:200] + "..."
        print(f"   Trecho: '{snip}'")
    else:
        print("   Trecho: ''")


def main():
    parser = argparse.ArgumentParser(description="Busca por similaridade em ementas (FAISS + SBERT).")
    parser.add_argument("--query", required=True, type=str, help="Texto da consulta")
    parser.add_argument("--top-k", type=int, default=10, help="Quantidade de resultados (default=10)")

    # Opção 1: apontar uma store (pasta com index.faiss + metadados.pkl)
    parser.add_argument("--store", type=str, default="data/store/ementas_faiss",
                        help="Diretório com index.faiss e metadados.pkl")

    # Opção 2: passar caminhos explícitos (sobrepõe --store)
    parser.add_argument("--index", type=str, default=None, help="Caminho para o arquivo index.faiss")
    parser.add_argument("--meta", type=str, default=None, help="Caminho para o arquivo metadados.pkl")

    # Saída em JSON
    parser.add_argument("--output-dir", type=str, default="data/results",
                        help="Diretório para salvar o JSON com os resultados")

    # Modelo de embeddings
    parser.add_argument("--model-name", type=str, default="sentence-transformers/all-MiniLM-L6-v2",
                        help="Nome do modelo SentenceTransformer (default=all-MiniLM-L6-v2)")

    args = parser.parse_args()

    store_dir = Path(args.store) if args.store else None
    index_path = Path(args.index) if args.index else None
    meta_path = Path(args.meta) if args.meta else None

    # Resolvido caminhos
    index_path, meta_path = load_store_paths(store_dir, index_path, meta_path)
    ensure_exists(index_path, "Índice FAISS")
    ensure_exists(meta_path, "Metadados")

    # Carregar tudo
    model = load_model(args.model_name)
    index = load_index(index_path)
    metadata = load_metadata(meta_path)

    # Checagem opcional: tamanho do índice vs metadados
    try:
        ntotal = index.ntotal
        if ntotal != len(metadata):
            print(f"⚠️ Aviso: index.ntotal={ntotal} difere do len(metadados)={len(metadata)}.")
    except Exception:
        pass

    # Embedding da query
    q = embed_query(model, args.query)

    # Busca
    dists, idxs = search(index, q, args.top_k)

    print("\n==== Top-K Resultados ====\n")
    results = []
    for rank, (dist, idx) in enumerate(zip(dists, idxs), start=1):
        if idx < 0 or idx >= len(metadata):
            # idx inválido (pode ocorrer se houve discrepância)
            row_meta = {"id": "", "title": "", "warning": "índice fora de range dos metadados"}
        else:
            row_meta = metadata[idx]

        # Imprime no console de forma amigável
        format_console_result(rank, float(dist), row_meta)

        # Armazena para JSON completo
        # Se row_meta tiver muitos campos, salvamos todos.
        results.append({
            "rank": rank,
            "score": float(dist),
            "index": int(idx),
            "metadata": row_meta
        })

    # Salvar JSON
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_json = output_dir / f"search_{ts}.json"

    payload = {
        "query": args.query,
        "top_k": args.top_k,
        "store": str(store_dir) if store_dir else None,
        "index_path": str(index_path),
        "meta_path": str(meta_path),
        "model_name": args.model_name,
        "results": results
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultados salvos em: {out_json}\n")


if __name__ == "__main__":
    main()
