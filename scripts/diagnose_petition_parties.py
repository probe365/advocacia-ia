"""Diagnóstico de contexto de petições (autor/réu/cliente/adverso).

Uso:
  set DEFAULT_TENANT_ID=public
  python scripts/diagnose_petition_parties.py
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cadastro_manager import CadastroManager
from app.services.petition_service import PetitionService


def _is_missing_party(p: Dict[str, Any]) -> bool:
    if not p:
        return True
    nome = (p.get("nome_completo") or "").strip()
    cpf = (p.get("cpf_cnpj") or "").strip()
    return not nome and not cpf


def _summarize_party(p: Dict[str, Any]) -> Dict[str, str]:
    return {
        "nome": (p.get("nome_completo") or "").strip(),
        "cpf_cnpj": (p.get("cpf_cnpj") or "").strip(),
        "email": (p.get("email") or "").strip(),
        "endereco": (p.get("endereco_completo") or "").strip(),
    }


def main() -> None:
    tenant_id = (os.getenv("DEFAULT_TENANT_ID") or "public").strip()
    mgr = CadastroManager(tenant_id=tenant_id)
    service = PetitionService()

    processos = mgr._execute_query(
        "SELECT id_processo, tipo_parte FROM processos WHERE tenant_id = %s",
        (tenant_id,),
        fetch="all",
    ) or []

    if not processos:
        print(f"Nenhum processo encontrado para tenant_id={tenant_id}")
        return

    total = 0
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []

    for proc in processos:
        total += 1
        pid = str(proc.get("id_processo"))
        ctx = service.preparar_contexto_peticao(tenant_id, pid) or {}
        autor = ctx.get("autor") or {}
        reu = ctx.get("reu") or {}
        missing_autor = _is_missing_party(autor)
        missing_reu = _is_missing_party(reu)

        autor_summary = _summarize_party(autor)
        reu_summary = _summarize_party(reu)

        print(
            f"processo={pid} tipo_parte={proc.get('tipo_parte')} "
            f"autor_nome={autor_summary['nome'] or '-'} "
            f"autor_cpf={autor_summary['cpf_cnpj'] or '-'} "
            f"autor_email={autor_summary['email'] or '-'} "
            f"autor_endereco={autor_summary['endereco'] or '-'} "
            f"reu_nome={reu_summary['nome'] or '-'} "
            f"reu_cpf={reu_summary['cpf_cnpj'] or '-'} "
            f"reu_email={reu_summary['email'] or '-'} "
            f"reu_endereco={reu_summary['endereco'] or '-'}"
        )

        rows.append(
            {
                "tenant_id": tenant_id,
                "processo": pid,
                "tipo_parte": proc.get("tipo_parte"),
                "autor_nome": autor_summary["nome"],
                "autor_cpf_cnpj": autor_summary["cpf_cnpj"],
                "autor_email": autor_summary["email"],
                "autor_endereco": autor_summary["endereco"],
                "reu_nome": reu_summary["nome"],
                "reu_cpf_cnpj": reu_summary["cpf_cnpj"],
                "reu_email": reu_summary["email"],
                "reu_endereco": reu_summary["endereco"],
                "missing_autor": missing_autor,
                "missing_reu": missing_reu,
            }
        )
        if missing_autor or missing_reu:
            issues.append(
                f"processo={pid} tipo_parte={proc.get('tipo_parte')} missing_autor={missing_autor} missing_reu={missing_reu}"
            )

    print(f"Processos analisados: {total}")
    if issues:
        print("Problemas encontrados:")
        for line in issues:
            print(f" - {line}")
    else:
        print("Nenhum problema encontrado.")

    if rows:
        out_dir = ROOT / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "diagnose_petition_parties.csv"
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV gerado: {out_path}")


if __name__ == "__main__":
    main()
