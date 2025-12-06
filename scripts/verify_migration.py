#!/usr/bin/env python
"""Verify that tipo_parte column was created successfully"""
import os
import sys

# Set environment variables
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')

try:
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
    
    # Check if tipo_parte column exists
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'processos' AND column_name = 'tipo_parte'
    """)
    
    result = cursor.fetchone()
    
    if result:
        print("\n✅ SUCCESS: tipo_parte column exists!")
        print(f"   Column Name: {result['column_name']}")
        print(f"   Data Type: {result['data_type']}")
        print(f"   Nullable: {result['is_nullable']}")
    else:
        print("\n❌ ERROR: tipo_parte column NOT found!")
        sys.exit(1)
    
    # Check if index exists
    cursor.execute("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'processos' AND indexname = 'ix_processos_tipo_parte'
    """)
    
    index_result = cursor.fetchone()
    
    if index_result:
        print(f"✅ SUCCESS: Index ix_processos_tipo_parte exists!")
    else:
        print("⚠️  WARNING: Index ix_processos_tipo_parte NOT found (might be OK)")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 Migration verification complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
