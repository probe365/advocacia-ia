from __future__ import annotations

import glob
import hashlib
from pathlib import Path
from typing import List, Optional


def candidate_case_ids(case_id: str) -> List[str]:
    """Return likely directory names for a given case identifier."""
    raw = (case_id or "").strip()
    if not raw:
        return []

    candidates: List[str] = []

    def _add(cid: str) -> None:
        if cid and cid not in candidates:
            candidates.append(cid)

    _add(raw)
    if not raw.startswith("caso_"):
        _add(f"caso_{raw}")

    # Mirror processos._compute_case_code behaviour (sha1 short hash)
    try:
        hashed = "caso_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
        _add(hashed)
    except Exception:
        pass

    return candidates


def base_case_dirs(tenant_id: Optional[str]) -> List[Path]:
    """Return the ordered list of directories to scan for case files."""
    tenant_segment = str(tenant_id) if tenant_id else "default"
    dirs = [
        Path("cases") / tenant_segment,
        Path("data/cases") / tenant_segment,
        Path("cases"),
        Path("data/cases"),
    ]
    return dirs


def _read_text_if_exists(path: Path) -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""
    return ""


def _latest_summary_from_cache(cache_dir: Path) -> str:
    try:
        paths = sorted(glob.glob(str(cache_dir / "summary_*.txt")))
        if not paths:
            return ""
        newest = max(paths, key=lambda p: Path(p).stat().st_mtime)
        return _read_text_if_exists(Path(newest))
    except Exception:
        return ""


def get_case_summary(case_id: str, tenant_id: Optional[str] = None, allow_pipeline: bool = True) -> str:
    """Best-effort retrieval of the resumo for a case, with pipeline fallback."""
    candidates = candidate_case_ids(case_id)
    if not candidates:
        return ""

    dirs = base_case_dirs(tenant_id)
    existing_case_id: Optional[str] = None

    for cid in candidates:
        for base_dir in dirs:
            case_dir = base_dir / cid
            if case_dir.exists() and existing_case_id is None:
                existing_case_id = cid

            resumo_txt = _read_text_if_exists(case_dir / "resumo.txt")
            if resumo_txt:
                return resumo_txt

            cache_txt = _latest_summary_from_cache(case_dir / "cache")
            if cache_txt:
                return cache_txt

    if not allow_pipeline:
        return ""

    try:
        from pipeline import Pipeline

        pipeline_case_id = existing_case_id or next(
            (cid for cid in candidates if cid.startswith("caso_")),
            candidates[0],
        )
        pipeline = Pipeline(case_id=pipeline_case_id, tenant_id=tenant_id)
        resumo, _ = pipeline.summarize_with_cache("Resumo geral do caso")
        return (resumo or "").strip()
    except Exception:
        return ""
