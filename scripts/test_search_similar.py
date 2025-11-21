"""
test_search_similar.py
Consulta o índice FAISS local (ementas_faiss/) para buscar ementas por similaridade sem usar o app Flask.
"""

import argparse
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# ========================
# Argumentos de linha
# ========================
parser = argparse.ArgumentParser(description="Busca ementas por similaridade no índice FAISS local.")
parser.add_argument("--query", type=str, required=True, help="Texto da ementa ou tese a buscar")
parser.add_argument("--top-k", type=int, default=5, help="Número de resultados mais similares")
parser.add_argument("--store-dir", type=str, default="data/store/ementas_faiss", help="Pasta do índice FAISS")
args = parser.parse_args()

# ========================
# Carregamento do modelo
# ========================
print("🔹 Carregando modelo de embeddings (SentenceTransformer)...")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# ========================
# Carrega o índice FAISS e metadados
# ========================
index_path = f"{args.store_dir}/index.faiss"
meta_path = f"{args.store_dir}/metadados.pkl"

print(f"🔹 Carregando índice FAISS de: {index_path}")
index = faiss.read_index(index_path)

print(f"🔹 Carregando metadados de: {meta_path}")
with open(meta_path, "rb") as f:
    metadados = pickle.load(f)

# ========================
# Gera embedding da consulta
# ========================
query_vec = model.encode([args.query], convert_to_numpy=True, normalize_embeddings=True)
D, I = index.search(query_vec, args.top_k)

# ========================
# Exibe resultados
# ========================
print("\n== Resultados de Similaridade ==")
for rank, (idx, score) in enumerate(zip(I[0], D[0])):
    if idx < 0 or idx >= len(metadados):
        continue
    doc = metadados[idx]
    print(f"\n[{rank+1}] score={score:.4f}")
    print(f"🔸 ID: {doc.get('id', 'N/A')}")
    print(f"🔸 Título: {doc.get('title', 'N/A')}")
    print(f"🔸 Grupo: {doc.get('metadados', {}).get('grupo', 'N/A')}")
    print(f"🔸 Órgão: {doc.get('metadados', {}).get('orgao', 'N/A')}")
    print(f"🔸 Data decisão: {doc.get('metadados', {}).get('data_decisao', 'N/A')}")
    print(f"🧾 Texto: {doc.get('text', '')[:500]}...")
