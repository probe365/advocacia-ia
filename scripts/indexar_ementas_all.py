# scripts/indexar_ementas_all.py
"""
Indexa ementas no backend /ementas (FAISS local) a partir de:
- CSV (STJ)
- Pasta com PDFs/TXTs

Uso (PowerShell):
  python scripts/indexar_ementas_all.py `
    --api http://127.0.0.1:5001 `
    --csv data/interim/stj_ementas.csv `
    --csv-text-col ementa `
    --csv-title-col titulo `
    --csv-id-col id_decisao `
    --folder data/ementas `
    --batch 200

Se quiser só CSV, remova --folder. Se quiser só pasta, remova --csv.
"""

from __future__ import annotations
import os, sys, glob, json, time, argparse
import requests
import pandas as pd
from typing import List, Dict
from pypdf import PdfReader

DEFAULT_API = os.environ.get("AIAPP_API_BASE", "http://127.0.0.1:5001")
INDEX_URL    = "{base}/ementas/index"


def log(msg: str) -> None:
    print(msg, flush=True)


def read_pdf_text(path: str) -> str:
    try:
        r = PdfReader(path)
        return "\n".join([(p.extract_text() or "") for p in r.pages])
    except Exception as e:
        return ""


def load_from_csv(csv_path: str, text_col: str, title_col: str | None, id_col: str | None) -> List[Dict]:
    if not os.path.exists(csv_path):
        log(f"⚠️  CSV não encontrado: {csv_path}")
        return []
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        text  = str(row[text_col]) if text_col in row and pd.notna(row[text_col]) else ""
        if not text.strip():
            continue
        title = str(row[title_col]) if title_col and title_col in row and pd.notna(row[title_col]) else None
        doc_id = str(row[id_col]) if id_col and id_col in row and pd.notna(row[id_col]) else None
        docs.append({
            "id": doc_id,
            "title": title,
            "text": text,
            "metadados": {"src": "csv", "csv": os.path.basename(csv_path)}
        })
    return docs


def load_from_folder(folder: str) -> List[Dict]:
    if not folder or not os.path.isdir(folder):
        log(f"⚠️  Pasta não encontrada: {folder}")
        return []
    paths = glob.glob(os.path.join(folder, "**", "*.*"), recursive=True)
    docs = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        text = ""
        try:
            if ext in [".txt", ".md"]:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif ext == ".pdf":
                text = read_pdf_text(p)
            else:
                continue
        except Exception:
            continue
        if not text or not text.strip():
            continue
        docs.append({
            "id": p,  # caminho como id
            "title": os.path.basename(p),
            "text": text,
            "metadados": {"src": "file", "path": p}
        })
    return docs


def post_batch(base_url: str, docs: List[Dict], batch: int = 200, timeout: int = 60) -> int:
    url = INDEX_URL.format(base=base_url.rstrip("/"))
    total_indexed = 0
    for i in range(0, len(docs), batch):
        part = docs[i:i+batch]
        try:
            r = requests.post(url, json={"docs": part}, timeout=timeout)
            r.raise_for_status()
            indexed = int(r.json().get("indexed", 0))
            total_indexed += indexed
            log(f"Indexed batch {i//batch+1}: +{indexed} (total={total_indexed})")
        except requests.HTTPError as e:
            # Mostra resposta do servidor para facilitar debug
            body = ""
            try:
                body = r.text[:400]
            except Exception:
                pass
            log(f"❌ HTTP {r.status_code} ao enviar batch {i//batch+1}: {body}")
            # continua nos próximos lotes
        except Exception as e:
            log(f"❌ Erro ao enviar batch {i//batch+1}: {e}")
    return total_indexed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", type=str, default=DEFAULT_API, help="Base da API (ex: http://127.0.0.1:5001)")
    ap.add_argument("--csv", type=str, help="Caminho do CSV (STJ)")
    ap.add_argument("--csv-text-col", type=str, default="ementa")
    ap.add_argument("--csv-title-col", type=str, default=None)
    ap.add_argument("--csv-id-col", type=str, default=None)
    ap.add_argument("--folder", type=str, help="Pasta com PDFs/TXTs")
    ap.add_argument("--batch", type=int, default=200)
    args = ap.parse_args()

    log("==> Indexando CSV (STJ) + PDFs/TXTs (FAISS)")
    docs: List[Dict] = []

    if args.csv:
        log(f"Carregando CSV: {args.csv}")
        csv_docs = load_from_csv(args.csv, args.csv_text_col, args.csv_title_col, args.csv_id_col)
        log(f" - CSV: {len(csv_docs)} docs")
        docs.extend(csv_docs)

    if args.folder:
        log(f"Varredura da pasta: {args.folder}")
        file_docs = load_from_folder(args.folder)
        log(f" - Arquivos: {len(file_docs)} docs")
        docs.extend(file_docs)

    log(f"Total a indexar: {len(docs)}")
    if not docs:
        log("Nada a indexar. Encerrando.")
        return

    total = post_batch(args.api, docs, batch=args.batch)
    log("Concluído.")
    log(f"Total inserido: {total}")


if __name__ == "__main__":
    main()
