#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script temporário para verificar se tabela partes_adversas existe"""
import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        dbname='advocacia_ia',
        user='postgres',
        password='postgres'
    )
    cur = conn.cursor()
    
    # Verificar se tabela existe
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'partes_adversas' 
        ORDER BY ordinal_position
    """)
    
    cols = cur.fetchall()
    
    if cols:
        print("✅ Tabela 'partes_adversas' EXISTE!")
        print(f"   Total de colunas: {len(cols)}\n")
        for col, dtype in cols:
            print(f"   - {col}: {dtype}")
    else:
        print("❌ Tabela 'partes_adversas' NÃO EXISTE!")
        print("   Execute: python alembic/versions/0006_create_partes_adversas.py")
    
    conn.close()

except Exception as e:
    print(f"❌ ERRO: {e}")
