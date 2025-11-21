# -*- coding: utf-8 -*-
"""
Verify and initialize pgvector extension in PostgreSQL (Windows & Cross-platform)
Run this script to enable pgvector in your database.
"""
import psycopg2
import sys
import subprocess
import os
from pathlib import Path

try:
    from config import get_config
except ImportError:
    print("❌ Error: config.py not found. Running from project root.")
    sys.exit(1)


def check_postgresql_service():
    """Check if PostgreSQL service is running on Windows."""
    try:
        result = subprocess.run(
            ["sc", "query", "postgresql-x64-18"],
            capture_output=True,
            text=True
        )
        if "RUNNING" in result.stdout:
            print("✅ PostgreSQL service is running")
            return True
        else:
            print("⚠️  PostgreSQL service is stopped")
            print("   Run: net start postgresql-x64-18")
            return False
    except Exception as e:
        print(f"⚠️  Could not check PostgreSQL service: {e}")
        return None


def check_pgvector_dll():
    """Check if vector.dll exists in PostgreSQL library directory."""
    try:
        result = subprocess.run(
            ["pg_config", "--pkglibdir"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pkglib = result.stdout.strip()
            vector_dll = Path(pkglib) / "vector.dll"
            vector_so = Path(pkglib) / "vector.so"
            
            if vector_dll.exists():
                print(f"✅ vector.dll found: {vector_dll}")
                return True
            elif vector_so.exists():
                print(f"✅ vector.so found: {vector_so}")
                return True
            else:
                print(f"❌ vector extension library not found in {pkglib}")
                print("   Please run: install_pgvector_windows.bat")
                return False
    except Exception as e:
        print(f"❌ Error checking pgvector library: {e}")
        return False


def enable_pgvector_extension(conn, cursor):
    """Create pgvector extension in the database."""
    try:
        print("📥 Creating pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        print("✅ pgvector extension created/already exists")
        return True
    except psycopg2.errors.ObjectNotInCatalog as e:
        print(f"❌ Error: pgvector not available in PostgreSQL")
        print(f"   Details: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating extension: {e}")
        return False


def create_embeddings_schema(conn, cursor):
    """Create embeddings schema (optional but recommended)."""
    try:
        print("📁 Creating embeddings schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS embeddings;")
        
        # Create a sample embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings.documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for faster similarity search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_embedding 
            ON embeddings.documents 
            USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100);
        """)
        
        conn.commit()
        print("✅ embeddings schema and sample table created")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not create schema: {e}")
        return False


def verify_pgvector(conn, cursor):
    """Verify pgvector installation."""
    try:
        cursor.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'vector'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ pgvector {result[1]} is installed and active")
            
            # Test basic vector operations
            try:
                cursor.execute("SELECT '[1,2,3]'::vector;")
                test_result = cursor.fetchone()
                print(f"✅ Basic vector operation works: {test_result[0]}")
                return True
            except Exception as e:
                print(f"⚠️  Vector operations test failed: {e}")
                return False
        else:
            print("❌ pgvector extension not found")
            return False
    except Exception as e:
        print(f"❌ Error verifying pgvector: {e}")
        return False


def init_pgvector():
    """Main initialization function."""
    cfg = get_config()()
    
    print("=" * 60)
    print("  pgvector Extension Initialization")
    print("=" * 60)
    print()
    
    # Check system prerequisites
    print("[STEP 1/5] Checking system requirements...")
    print(f"  Database: {cfg.DB_HOST}:{cfg.DB_PORT}/{cfg.DB_NAME}")
    print(f"  User: {cfg.DB_USER}")
    print()
    
    # Check PostgreSQL service
    print("[STEP 2/5] Checking PostgreSQL service...")
    service_status = check_postgresql_service()
    if service_status is False:
        print("❌ PostgreSQL service is not running")
        return False
    print()
    
    # Check pgvector library
    print("[STEP 3/5] Checking pgvector library installation...")
    if not check_pgvector_dll():
        print("❌ pgvector library not found. Installation needed.")
        return False
    print()
    
    # Connect to database
    print("[STEP 4/5] Connecting to database...")
    try:
        # First connect to postgres database
        print("  Connecting to 'postgres' database...")
        conn = psycopg2.connect(
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            database="postgres",
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD,
            connect_timeout=5
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create target database if needed
        print(f"  Creating database '{cfg.DB_NAME}' if needed...")
        try:
            cursor.execute(f"CREATE DATABASE {cfg.DB_NAME};")
            print(f"✅ Database '{cfg.DB_NAME}' created")
        except psycopg2.errors.DuplicateDatabase:
            print(f"✅ Database '{cfg.DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        
        # Connect to target database
        print(f"  Connecting to '{cfg.DB_NAME}' database...")
        conn = psycopg2.connect(
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            database=cfg.DB_NAME,
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD,
            connect_timeout=5
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected to database")
        print()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("   Ensure PostgreSQL is running and credentials are correct")
        return False
    
    # Enable pgvector extension
    print("[STEP 5/5] Configuring pgvector...")
    
    if not enable_pgvector_extension(conn, cursor):
        cursor.close()
        conn.close()
        return False
    
    # Create schemas
    create_embeddings_schema(conn, cursor)
    
    # Verify
    if not verify_pgvector(conn, cursor):
        cursor.close()
        conn.close()
        return False
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("  ✅ pgvector initialization complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Your database is ready for vector operations")
    print("2. Use embeddings.documents table for storing documents with embeddings")
    print("3. Example query:")
    print("   SELECT * FROM embeddings.documents")
    print("   ORDER BY embedding <=> '[1,2,3,...]'::vector")
    print("   LIMIT 5;")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = init_pgvector()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
