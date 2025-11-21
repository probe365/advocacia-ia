#!/usr/bin/env python
"""Get existing client to use for testing"""
import os
import psycopg2
from psycopg2.extras import DictCursor

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')

try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )
    
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # First check clientes table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'clientes'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("📋 Clientes table structure:")
    for col in columns:
        print(f"   {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    # Get existing clients - dynamically using first column
    if columns:
        first_col = columns[0]['column_name']
        cursor.execute(f"SELECT * FROM clientes LIMIT 5")
        clientes = cursor.fetchall()
        
        if clientes:
            print(f"\n✅ Existing clients:")
            for cliente in clientes:
                print(f"   {dict(cliente)}")
        else:
            print("❌ No clients found. Need to create one.")
    
    # Check processos table structure
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'processos'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print("\n📋 Processos table structure:")
    for col in columns:
        print(f"   {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
