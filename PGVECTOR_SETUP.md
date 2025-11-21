# pgvector Installation & Configuration Guide

## Overview
`pgvector` is a PostgreSQL extension that enables vector operations and similarity search. It's essential for semantic search and embedding-based queries.

---

## Installation Methods

### ✅ Method 1: Docker (Recommended - What we just set up)

**What we changed:**
1. Updated `docker-compose.yml` to use `pgvector/pgvector:pg16` image
2. Created `init-pgvector.sql` initialization script
3. pgvector extension is automatically created on container startup

**To use:**
```bash
docker-compose down
docker-compose up -d db
```

Verify:
```bash
docker-compose exec db psql -U advuser -d advia -c "CREATE EXTENSION IF NOT EXISTS vector; \dx vector"
```

---

### Method 2: Local PostgreSQL Installation (Ubuntu/Debian)

**Prerequisites:**
- PostgreSQL 16+ installed
- Build tools available

**Installation:**
```bash
# Option A: Using the script we created
bash install_pgvector.sh

# Option B: Manual installation
sudo apt-get install postgresql-contrib postgresql-server-dev-16 build-essential git
cd /tmp
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Enable the extension:**
```bash
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### Method 3: Manual PostgreSQL Connection (Any OS)

**Using Python:**
```bash
python init_pgvector_db.py
```

This script will:
- Connect to your PostgreSQL server
- Create the database if needed
- Create pgvector extension
- Create embeddings schema
- Verify installation

---

## Verification

### Check if pgvector is installed:

**Using psql:**
```bash
psql -U advuser -d advia -c "\dx vector"
```

Should output:
```
                          List of installed extensions
Name   | Version | Schema |                   Description
--------+---------+--------+--------------------------------------
vector | 0.6.0   | public | open-source vector similarity search
(1 row)
```

**Using Python:**
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="advia",
    user="advuser",
    password="advpass"
)
cursor = conn.cursor()
cursor.execute("CREATE EXTENSION IF NOT EXISTS vector; SELECT version();")
cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname='vector';")
print(cursor.fetchall())
cursor.close()
conn.close()
```

---

## Usage Example

### Create a table with vector column:

```sql
-- Create embeddings schema
CREATE SCHEMA IF NOT EXISTS embeddings;

-- Create documents table with vector column
CREATE TABLE embeddings.documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- 1536 is common for OpenAI embeddings
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster similarity search
CREATE INDEX ON embeddings.documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Insert embeddings:

```sql
INSERT INTO embeddings.documents (content, embedding) 
VALUES (
    'Your text here',
    '[0.1, 0.2, 0.3, ...]'::vector
);
```

### Search similar documents:

```sql
-- Find 5 most similar documents
SELECT id, content, embedding <-> query_embedding AS distance
FROM embeddings.documents
ORDER BY embedding <-> query_embedding
LIMIT 5;
```

---

## Vector Operations

pgvector supports three distance metrics:

| Operator | Name | Use Case |
|----------|------|----------|
| `<->` | L2 distance (Euclidean) | General purpose |
| `<=>` | Cosine distance | Text embeddings (default) |
| `<\|>` | Inner product | When embeddings are normalized |

---

## Integration with Python/Flask

### Using SQLAlchemy with pgvector:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import pgvector.sqlalchemy

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    embedding = Column(pgvector.sqlalchemy.Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document {self.id}>"

# Query similar documents
def find_similar(query_embedding, k=5):
    return (
        Document.query
        .order_by(Document.embedding.cosine_distance(query_embedding))
        .limit(k)
        .all()
    )
```

### Using psycopg2 directly:

```python
import psycopg2
import numpy as np

conn = psycopg2.connect(...)
cursor = conn.cursor()

# Insert embedding
embedding = np.array([0.1, 0.2, 0.3, ...]).tolist()
cursor.execute(
    "INSERT INTO embeddings.documents (content, embedding) VALUES (%s, %s)",
    ("Your text", str(embedding))
)

# Search similar
cursor.execute("""
    SELECT id, content, embedding <=> %s AS distance
    FROM embeddings.documents
    ORDER BY embedding <=> %s
    LIMIT 5
""", (str(query_embedding), str(query_embedding)))
results = cursor.fetchall()
```

---

## Troubleshooting

### Issue: Extension not found
```
ERROR: could not open extension control file
```
**Solution:** Make sure pgvector is installed on the system.

### Issue: Docker container won't start
```bash
# Check logs
docker-compose logs db

# Rebuild
docker-compose down
docker system prune -a
docker-compose up -d db
```

### Issue: Permission denied
```sql
-- Run as superuser or grant permissions
ALTER SCHEMA embeddings OWNER TO advuser;
GRANT ALL ON SCHEMA embeddings TO advuser;
```

---

## Files Modified/Created

1. ✅ `docker-compose.yml` - Updated PostgreSQL image to pgvector/pgvector:pg16
2. ✅ `init-pgvector.sql` - Initialization script for Docker
3. ✅ `install_pgvector.sh` - Manual installation script for Linux
4. ✅ `init_pgvector_db.py` - Python initialization script
5. 📄 `PGVECTOR_SETUP.md` - This guide

---

## Next Steps

1. **Start Docker containers:**
   ```bash
   docker-compose up -d
   ```

2. **Verify pgvector is active:**
   ```bash
   python init_pgvector_db.py
   ```

3. **Create embeddings tables** in your migration or initialization script

4. **Update your Flask models** to include vector columns

---

## References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector Documentation](https://github.com/pgvector/pgvector#getting-started)
- [PostgreSQL Vector Type](https://www.postgresql.org/docs/current/sql-types.html)
