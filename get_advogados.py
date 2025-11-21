#!/usr/bin/env python
"""Get existing lawyers/advogados"""
import os
import psycopg2
from psycopg2.extras import DictCursor

os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'advocacia_ia')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'probe365')
os.environ.setdefault('DB_PORT', '5432')

conn = psycopg2.connect(
    host=os.environ.get('DB_HOST'),
    database=os.environ.get('DB_NAME'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    port=os.environ.get('DB_PORT')
)

cursor = conn.cursor(cursor_factory=DictCursor)

# Get advogados table structure
cursor.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'advogados'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
print("Advogados table columns:")
for col in columns:
    print(f"  {col['column_name']}")

# Get existing advogados
cursor.execute("SELECT * FROM advogados LIMIT 5")
advogados = cursor.fetchall()

print("\nExisting advogados:")
for adv in advogados:
    print(f"  {dict(adv)}")

cursor.close()
conn.close()
