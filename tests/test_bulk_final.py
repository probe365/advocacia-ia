#!/usr/bin/env python
"""Test bulk upload with tipo_parte using real client"""
import os
import sys

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DEFAULT_TENANT_ID', 'public')

try:
    from cadastro_manager import CadastroManager
    import psycopg2
    from psycopg2.extras import DictCursor
    
    # Get first existing client
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT id_cliente, nome_completo FROM clientes LIMIT 1")
    cliente = cursor.fetchone()
    
    if not cliente:
        print("❌ ERROR: No clients found in database")
        sys.exit(1)
    
    id_cliente = cliente['id_cliente']
    nome_cliente = cliente['nome_completo']
    print(f"✅ Using client: {nome_cliente} (ID: {id_cliente})")
    
    # Initialize manager
    manager = CadastroManager(tenant_id=os.environ.get('DEFAULT_TENANT_ID'))
    
    # Read test CSV
    with open('test_bulk_upload_real.csv', 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
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
    
    # Verify in database
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
            print(f"      • {row['nome_caso']}: tipo_parte='{row['tipo_parte']}', advogado='{row['advogado_oab']}'")
    else:
        print(f"   ⚠️  No processos with tipo_parte found")
    
    # Check distribution
    cursor.execute("""
        SELECT tipo_parte, COUNT(*) as count
        FROM processos 
        WHERE id_cliente = %s AND tipo_parte IS NOT NULL
        GROUP BY tipo_parte
    """, (id_cliente,))
    
    distribution = cursor.fetchall()
    if distribution:
        print(f"\n   📊 Distribution by tipo_parte:")
        for dist in distribution:
            print(f"      • {dist['tipo_parte']}: {dist['count']}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Test complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
