#!/usr/bin/env python
"""Teste rápido de partes adversas."""
from __future__ import annotations

import os
import sys
from psycopg2 import OperationalError

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_partes_check(skip_on_db_error: bool = False) -> None:
    """Executa o diagnóstico de partes adversas."""
    from cadastro_manager import CadastroManager
    import psycopg2

    try:
        mgr = CadastroManager(tenant_id="public")
        partes = mgr.get_partes_adversas_by_processo("caso_11b044bc")
    except OperationalError as error:
        if skip_on_db_error:
            import pytest

            pytest.skip(f"Partes adversas test skipped: {error}")
        raise

    print(f"\n✅ Partes encontradas: {len(partes) if partes else 0}")
    print(f"   tenant_id usado: {mgr.tenant_id}")
    print(f"   multi_tenant: {mgr.multi_tenant}\n")

    if partes:
        for parte in partes:
            print(
                f"   ID: {parte.get('id')} - {parte.get('nome_completo')} ({parte.get('tipo_parte')})"
            )
            print(f"      tenant_id: {parte.get('tenant_id')}")
            print()
        return

    print("   ❌ Nenhuma parte encontrada!\n")

    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            dbname=os.environ.get("DB_NAME", "advocacia_ia"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "postgres"),
            port=os.environ.get("DB_PORT", "5432"),
        )
    except OperationalError as error:
        if skip_on_db_error:
            import pytest

            pytest.skip(f"Partes adversas test skipped: {error}")
        raise

    with conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nome_completo, tenant_id FROM partes_adversas WHERE id_processo = %s",
            ("caso_11b044bc",),
        )
        todas = cur.fetchall()

    print(f"   📊 Total no banco (sem filtro): {len(todas)}")
    for registro in todas:
        print(f"      ID {registro[0]}: {registro[1]} (tenant_id={registro[2]})")


def test_partes() -> None:
    run_partes_check(skip_on_db_error=True)


def main() -> None:
    try:
        run_partes_check(skip_on_db_error=False)
    except OperationalError as error:
        print(f"\n❌ ERRO: {error}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
