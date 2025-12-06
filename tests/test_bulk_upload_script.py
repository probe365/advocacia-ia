#!/usr/bin/env python
"""Smoke test for bulk upload with tipo_parte."""
import os
import sys
from pathlib import Path
from typing import Optional
from psycopg2 import OperationalError

# Ensure top-level modules remain importable when pytest moves cwd
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DEFAULT_TENANT_ID', 'public')


CSV_CANDIDATES = (
    Path(__file__).resolve().parent / 'test_bulk_upload.csv',
    PROJECT_ROOT / 'test_bulk_upload.csv',
    PROJECT_ROOT / 'docs' / 'test_bulk_upload.csv',
    PROJECT_ROOT / 'docs' / 'test_bulk_upload_real.csv',
)


def _find_csv_path() -> Optional[Path]:
    for candidate in CSV_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def run_bulk_upload_script(skip_on_missing_deps: bool = False) -> None:
    """Execute the legacy bulk upload smoke test."""
    from cadastro_manager import CadastroManager
    import psycopg2
    from psycopg2.extras import DictCursor

    csv_path = _find_csv_path()
    if not csv_path:
        message = "test_bulk_upload.csv not found in tests/ or docs/"
        if skip_on_missing_deps:
            import pytest
            pytest.skip(message)
        raise FileNotFoundError(message)

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
        except OperationalError as db_error:
            if skip_on_missing_deps:
                import pytest
                pytest.skip(f"Bulk upload script skipped: {db_error}")
            raise

        manager = CadastroManager(
            tenant_id=os.environ.get('DEFAULT_TENANT_ID')
        )

        print("\n📋 Testing bulk upload with tipo_parte...")
        csv_content = csv_path.read_text(encoding='utf-8')
        resultado = manager.bulk_create_processos_from_csv('test_client_123', csv_content)

        print("\n✅ Result:")
        print(f"   Processos criados: {resultado.get('processos_criados', 0)}")

        if resultado.get('erros'):
            print(f"   Erros: {len(resultado['erros'])}")
            for erro in resultado['erros']:
                print(f"      - {erro}")
        else:
            print("   Erros: 0 ✅")

        print("\n📊 Verifying data in database...")
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute("""
            SELECT nome_caso, tipo_parte FROM processos 
            WHERE tipo_parte IS NOT NULL 
            ORDER BY id DESC LIMIT 3
        """)

        rows = cursor.fetchall()
        print("\n   Last 3 processos with tipo_parte:")
        for row in rows:
            print(f"      ✓ {row['nome_caso']}: {row['tipo_parte']}")

        cursor.close()
        print("\n🎉 Bulk upload test complete!")

    finally:
        if conn:
            conn.close()


def test_bulk_upload_script() -> None:
    run_bulk_upload_script(skip_on_missing_deps=True)


def main() -> None:
    try:
        run_bulk_upload_script(skip_on_missing_deps=False)
    except Exception as exc:  # pragma: no cover - CLI mode
        print(f"\n❌ ERROR: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
