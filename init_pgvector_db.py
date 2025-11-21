# -*- coding: utf-8 -*-
"""
Initialize pgvector extension in PostgreSQL database.
Run this after starting your database to ensure the extension is created.
"""
import psycopg2
import sys
from config import get_config

def init_pgvector():
    """Create pgvector extension in the database."""
    cfg = get_config()()
    
    try:
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            database="postgres",  # Connect to postgres database first
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create the target database if it doesn't exist
        print(f"📦 Ensuring database '{cfg.DB_NAME}' exists...")
        cursor.execute(f"CREATE DATABASE {cfg.DB_NAME};")
        print(f"   ✓ Database created (or already exists)")
        cursor.close()
        conn.close()
        
        # Connect to the target database
        print(f"🔗 Connecting to database '{cfg.DB_NAME}'...")
        conn = psycopg2.connect(
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            database=cfg.DB_NAME,
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create pgvector extension
        print("📥 Creating pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("   ✓ pgvector extension created")
        
        # Create embeddings schema (optional but recommended)
        print("📁 Creating embeddings schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS embeddings;")
        print("   ✓ embeddings schema created")
        
        # Verify installation
        print("✅ Verifying pgvector installation...")
        cursor.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'vector'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"   ✓ pgvector {result[1]} is installed and active")
            return True
        else:
            print("   ⚠️  pgvector extension not found!")
            return False
        
        cursor.close()
        conn.close()
        
    except psycopg2.errors.DuplicateDatabase:
        print(f"   ✓ Database '{cfg.DB_NAME}' already exists")
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS embeddings;")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = init_pgvector()
    sys.exit(0 if success else 1)
