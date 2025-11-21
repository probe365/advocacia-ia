#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Indexador FAISS para ementas (CSV + pasta de PDFs/TXTs), salvando:
 - index.faiss
 - metadados.pkl  (com texto/ementa incluído)
 - metadados.schema.json

Principais recursos:
 - Suporte a CSV com colunas configuráveis (inclua quantas extras quiser)
 - Varredura de pasta com PDFs/TXTs (tenta várias libs para PDF)
 - Normalização opcional (padrão: ligada) p/ simular coseno em FAISS (IP)
 - Lote/batch configurável
 - Deduplicação por ID (caso existam repetidos)
 - Compatível com Windows (paths absolutos/relativos OK)
"""

import os
import sys
import csv
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from tqdm import tqdm

# sentence-transformers
from sentence_transformers import SentenceTransformer

# FAISS
import faiss


# ----------------------------
# Utilidades de leitura de PDF
# ----------------------------
def read_pdf_text(path: str) -> str:
    """
    Tenta extrair texto de um PDF via PyPDF2, pdfplumber, pdfminer.six (nessa ordem),
    usando o que estiver disponível. Se tudo falhar, retorna string vazia.
    """
    text = ""

    # 1) PyPDF2
    try:
        import PyPDF2  # type: ignore
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            parts = []
            for page in reader.pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception:
                    parts.append("")
            text = "\n".join(parts).strip()
        if text:
            return text
    except Exception:
        pass

    # 2) pdfplumber
    try:
        import pdfplumber  # type: ignore
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception:
                    parts.append("")
        text = "\n".join(parts).strip()
        if text:
            return text
    except Exception:
        pass

    # 3) pdfminer.six (low-level)
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        text = extract_text(path) or ""
        text = text.strip()
        if text:
            return text
    except Exception:
        pass

    return ""


def read_txt_text(path: str, encoding: str = "utf-8") -> str:
    try:
        with open(path, "r", encoding=encoding, errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


# ----------------------------
# Carregamento de CSV
# ----------------------------
def load_csv_docs(
    csv_path: str,
    text_col: str,
    id_col: str,
    title_col: Optional[str] = None,
    extra_cols: Optional[List[str]] = None,
    sep: str = ",",
    encoding: str = "utf-8",
) -> List[Dict[str, Any]]:
    """
    Lê CSV e devolve uma lista de metadados, incluindo o texto (ementa).
    """
    out: List[Dict[str, Any]] = []
    p = Path(csv_path)
    if not p.exists():
        print(f"⚠️  CSV não encontrado: {csv_path}\n - CSV: 0 docs")
        return out

    with open(p, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=sep)
        required_cols = {text_col, id_col}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            have = ", ".join(reader.fieldnames or [])
            need = ", ".join(sorted(required_cols))
            raise ValueError(
                f"CSV não contém as colunas obrigatórias. Tem: [{have}]  |  Precisa: [{need}]"
            )

        for row in reader:
            _id = str(row.get(id_col, "")).strip()
            text = (row.get(text_col) or "").strip()

            if not _id or not text:
                # pula linhas sem id ou sem texto
                continue

            meta = {
                "id": _id,
                "title": (row.get(title_col) or "").strip() if title_col else "",
                # guardamos o texto/ementa completo
                "text": text,
                "source": "csv",
                "path": "",  # CSV não tem path de arquivo
            }

            # adiciona extras (se pedidas e existirem)
            if extra_cols:
                for c in extra_cols:
                    meta[c] = row.get(c)

            out.append(meta)

    print(f" - CSV: {len(out)} docs")
    return out


# ----------------------------
# Varredura de Pasta
# ----------------------------
def scan_folder_docs(folder: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """
    Percorre a pasta coletando PDFs/TXTs, extrai texto e monta metadados.
    id = nome do arquivo (sem extensão)
    title = nome do arquivo
    text = conteúdo extraído
    """
    out: List[Dict[str, Any]] = []
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"⚠️  Pasta não encontrada: {folder}\n - Arquivos: 0 docs")
        return out

    files = list(folder_path.rglob("*"))
    pdf_or_txt = [p for p in files if p.suffix.lower() in [".pdf", ".txt"]]
    print(f"Varredura da pasta: {folder}\n - Arquivos encontrados: {len(pdf_or_txt)}")
    for p in pdf_or_txt:
        text = ""
        try:
            if p.suffix.lower() == ".pdf":
                text = read_pdf_text(str(p))
            elif p.suffix.lower() == ".txt":
                text = read_txt_text(str(p), encoding=encoding)
        except Exception:
            text = ""

        text = (text or "").strip()
        if not text:
            # se não conseguiu extrair texto, pula
            continue

        meta = {
            "id": p.stem,                  # ex.: 000123456
            "title": p.name,               # ex.: 000123456.pdf
            "text": text,                  # conteúdo do PDF/TXT
            "source": "folder",
            "path": str(p.resolve()),
        }
        out.append(meta)

    print(f" - Arquivos indexáveis (com texto): {len(out)} docs")
    return out


# ----------------------------
# Embeddings / FAISS
# ----------------------------
def make_faiss_index(
    dim: int,
    metric: str = "ip",
    normalize: bool = True,
):
    """
    Cria index FAISS.
    - Para coseno, usamos IndexFlatIP e normalizamos vetores (normalize=True).
    - Para L2, usamos IndexFlatL2 (normalize=False sugerido).
    """
    metric = metric.lower().strip()
    if metric == "l2":
        return faiss.IndexFlatL2(dim), False
    # default: inner-product (para coseno com normalize=True)
    return faiss.IndexFlatIP(dim), normalize


def embed_corpus(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = 64,
    normalize: bool = True,
    show_progress: bool = True,
) -> np.ndarray:
    """
    Gera embeddings. Se normalize=True, normaliza (L2) antes de retornar,
    ideal para simular cosseno com IndexFlatIP.
    """
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        device=model.device
    )
    if normalize:
        faiss.normalize_L2(vecs)
    return vecs.astype("float32")


def dedup_by_id(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicatas mantendo o primeiro de cada id.
    """
    seen = set()
    out = []
    for d in docs:
        _id = d.get("id")
        if _id in seen:
            continue
        seen.add(_id)
        out.append(d)
    return out


# ----------------------------
# Main
# ----------------------------
def parse_args():
    ap = argparse.ArgumentParser(description="Indexar ementas em FAISS (CSV + pasta).")

    # Entrada CSV
    ap.add_argument("--csv", type=str, default="", help="Caminho do CSV.")
    ap.add_argument("--csv-text-col", type=str, default="text", help="Nome da coluna de texto/ementa no CSV.")
    ap.add_argument("--csv-id-col", type=str, default="id", help="Nome da coluna de ID no CSV.")
    ap.add_argument("--csv-title-col", type=str, default="", help="Coluna usada como 'title' no CSV (opcional).")
    ap.add_argument("--csv-extra-cols", type=str, default="", help="Lista separada por vírgulas de colunas extras (ex: 'label,grupo,orgao,data_decisao').")
    ap.add_argument("--csv-sep", type=str, default=",", help="Separador do CSV.")
    ap.add_argument("--csv-encoding", type=str, default="utf-8", help="Encoding do CSV.")

    # Pasta
    ap.add_argument("--folder", type=str, default="", help="Pasta com PDFs/TXTs (opcional).")
    ap.add_argument("--folder-encoding", type=str, default="utf-8", help="Encoding para TXT da pasta.")

    # Modelo / Index
    ap.add_argument("--model", type=str, default="sentence-transformers/all-MiniLM-L6-v2", help="Modelo de embeddings.")
    ap.add_argument("--batch", type=int, default=64, help="Tamanho do batch de embeddings.")
    ap.add_argument("--metric", type=str, default="ip", choices=["ip", "l2"], help="Métrica FAISS.")
    ap.add_argument("--normalize", action="store_true", default=True, help="Normalizar vetores (recomendado p/ coseno).")
    ap.add_argument("--no-normalize", dest="normalize", action="store_false", help="Desliga normalização (não recomendado p/ coseno).")

    # Saída
    ap.add_argument("--store", type=str, default="data/store/ementas_faiss", help="Pasta de saída para index.faiss e metadados.")
    ap.add_argument("--force", action="store_true", help="Se existir índice, sobrescreve.")

    return ap.parse_args()


def main():
    args = parse_args()

    out_dir = Path(args.store)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.faiss"
    meta_path = out_dir / "metadados.pkl"
    schema_path = out_dir / "metadados.schema.json"

    if index_path.exists() and meta_path.exists() and not args.force:
        print(f"⚠️  Já existe índice em: {out_dir} (use --force para sobrescrever).")
        print(f" - {index_path}")
        print(f" - {meta_path}")
        return

    print("==> Indexando CSV (STJ) + PDFs/TXTs (FAISS)")

    # 1) CSV
    extras = [c.strip() for c in args.csv_extra_cols.split(",") if c.strip()] if args.csv_extra_cols else []
    csv_docs = []
    if args.csv:
        csv_docs = load_csv_docs(
            csv_path=args.csv,
            text_col=args.csv_text_col,
            id_col=args.csv_id_col,
            title_col=args.csv_title_col if args.csv_title_col else None,
            extra_cols=extras,
            sep=args.csv_sep,
            encoding=args.csv_encoding,
        )

    # 2) Pasta
    folder_docs = []
    if args.folder:
        folder_docs = scan_folder_docs(args.folder, encoding=args.folder_encoding)

    docs = (csv_docs or []) + (folder_docs or [])
    if not docs:
        print("Total a indexar: 0\nNada a indexar. Encerrando.")
        return

    # Dedup por id
    before = len(docs)
    docs = dedup_by_id(docs)
    removed = before - len(docs)
    if removed > 0:
        print(f"ℹ️  Removidas {removed} duplicatas por ID.")

    print(f"Total a indexar (sem duplicatas): {len(docs)}")

    # 3) Carrega modelo
    print("Carregando modelo de embeddings…")
    model = SentenceTransformer(args.model)
    try:
        device = "cuda" if model._target_device.type == "cuda" else "cpu"
    except Exception:
        device = "cpu"
    print(f" - device: {device}")

    # 4) Cria índice FAISS
    # Embedding de uma amostra para descobrir a dimensão
    tmp_vec = model.encode(["DIM_PROBE"], convert_to_numpy=True)
    dim = int(tmp_vec.shape[1])
    index, do_norm = make_faiss_index(dim=dim, metric=args.metric, normalize=args.normalize)

    # 5) Embeddings em lotes e adiciona ao índice
    texts = [d["text"] for d in docs]
    batch_size = max(8, int(args.batch))

    # Em datasets muito grandes, para evitar picos, fazemos por blocos
    all_vecs = []
    print("Gerando embeddings (pode demorar)…")
    for i in tqdm(range(0, len(texts), batch_size), total=(len(texts) + batch_size - 1)//batch_size):
        chunk = texts[i: i + batch_size]
        vecs = embed_corpus(model, chunk, batch_size=batch_size, normalize=do_norm, show_progress=False)
        all_vecs.append(vecs)

    X = np.vstack(all_vecs).astype("float32")
    assert X.shape[0] == len(docs), "Número de vetores difere do número de docs."

    print("Adicionando ao índice FAISS…")
    index.add(X)

    # 6) Salvar
    print("\n==> Salvando resultados…")
    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(docs, f)

    # Salvar esquema (chaves/colunas presentes)
    keys = sorted({k for d in docs for k in d.keys()})
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump({"keys": keys}, f, ensure_ascii=False, indent=2)

    print(f"\n✅ FAISS: {index_path}")
    print(f"✅ Metadados: {meta_path}")
    print(f"📄 Esquema: {schema_path}")
    print("🎉 Concluído.")


if __name__ == "__main__":
    main()
