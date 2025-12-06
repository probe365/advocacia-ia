#!/usr/bin/env python
"""Test bulk upload with tipo_parte using real client."""
import os
import sys
from pathlib import Path
from psycopg2 import OperationalError

# Ensure the repository root is importable when pytest sets cwd elsewhere
_current = Path(__file__).resolve().parent
for candidate in (_current, *_current.parents):
    if (candidate / "cadastro_manager.py").exists():
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)
        break

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DEFAULT_TENANT_ID', 'public')


def run_bulk_upload(skip_on_db_error: bool = False) -> None:
    """Execute the bulk upload validation, optionally skipping missing DB."""
    from cadastro_manager import CadastroManager
    import psycopg2
    from psycopg2.extras import DictCursor

    conn = None
    try:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST'),
                database=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                port=os.environ.get('DB_PORT')
            )
        except OperationalError as error:
            if skip_on_db_error:
                import pytest
                pytest.skip(f"Bulk upload test skipped: {error}")
            raise

        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT id_cliente, nome_completo FROM clientes LIMIT 1")
        cliente = cursor.fetchone()

        if not cliente:
            print("❌ ERROR: No clients found in database")
            sys.exit(1)

        id_cliente = cliente['id_cliente']
        nome_cliente = cliente['nome_completo']
        print(f"✅ Using client: {nome_cliente} (ID: {id_cliente})")

        manager = CadastroManager(tenant_id=os.environ.get('DEFAULT_TENANT_ID'))

        with open('test_bulk_upload_real.csv', 'r', encoding='utf-8') as file_handle:
            csv_content = file_handle.read()

        print(f"\n📋 Testing bulk upload with tipo_parte...")
        print(f"   CSV content:\n{csv_content}")

        resultado = manager.bulk_create_processos_from_csv(id_cliente, csv_content)

        print(f"\n✅ Upload Result:")
        print(f"   Processos created: {resultado.get('processos_criados', 0)}")

        if resultado.get('erros'):
            print(f"   Errors: {len(resultado['erros'])}")
            for erro in resultado['erros']:
                print(f"      ❌ {erro}")
        else:
            print(f"   Errors: 0 ✅")

        print(f"\n📊 Verifying data in database...")
        cursor.execute("""
            SELECT nome_caso, tipo_parte, advogado_oab
            FROM processos 
            WHERE id_cliente = %s AND tipo_parte IS NOT NULL
            ORDER BY id_processo DESC LIMIT 5
        """, (id_cliente,))

        rows = cursor.fetchall()
        if rows:
            print(f"   ✅ Found {len(rows)} processos with tipo_parte:")
            for row in rows:
                print(
                    f"      • {row['nome_caso']}: tipo_parte='{row['tipo_parte']}', advogado='{row['advogado_oab']}'"
                )
        else:
            print("   ⚠️  No processos with tipo_parte found")

        cursor.execute("""
            SELECT tipo_parte, COUNT(*) as count
            FROM processos 
            WHERE id_cliente = %s AND tipo_parte IS NOT NULL
            GROUP BY tipo_parte
        """, (id_cliente,))

        distribution = cursor.fetchall()
        if distribution:
            print("\n   📊 Distribution by tipo_parte:")
            for dist in distribution:
                print(f"      • {dist['tipo_parte']}: {dist['count']}")

        print("\n🎉 Test complete!")

    except OperationalError as error:
        if skip_on_db_error:
            import pytest
            pytest.skip(f"Bulk upload test skipped: {error}")
        raise
    finally:
        if conn:
            conn.close()


def test_bulk_final() -> None:
    """Pytest entry point."""
    run_bulk_upload(skip_on_db_error=True)


def main() -> None:
    try:
        run_bulk_upload(skip_on_db_error=False)
    except OperationalError as error:
        print(f"\n❌ ERROR: {error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
