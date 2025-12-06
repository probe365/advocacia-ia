#!/usr/bin/env python
"""Test the bulk upload with tipo_parte"""
import os
import sys
import csv

# Set environment variables
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DEFAULT_TENANT_ID', 'public')

try:
    from cadastro_manager import CadastroManager
    
    # Initialize manager
    manager = CadastroManager(
        tenant_id=os.environ.get('DEFAULT_TENANT_ID')
    )
    
    print("\n📋 Testing bulk upload with tipo_parte...")
    
    # Read test CSV
    with open('test_bulk_upload.csv', 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    resultado = manager.bulk_create_processos_from_csv('test_client_123', csv_content)
    
    print("\n✅ Result:")
    print(f"   Processos criados: {resultado.get('processos_criados', 0)}")
    
    if resultado.get('erros'):
        print(f"   Erros: {len(resultado['erros'])}")
        for erro in resultado['erros']:
            print(f"      - {erro}")
    else:
        print(f"   Erros: 0 ✅")
    
    # Verify in database
    print("\n📊 Verifying data in database...")
    
    import psycopg2
    from psycopg2.extras import DictCursor
    
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute("""
        SELECT nome_caso, tipo_parte FROM processos 
        WHERE tipo_parte IS NOT NULL 
        ORDER BY id DESC LIMIT 3
    """)
    
    rows = cursor.fetchall()
    print(f"\n   Last 3 processos with tipo_parte:")
    for row in rows:
        print(f"      ✓ {row['nome_caso']}: {row['tipo_parte']}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Bulk upload test complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
