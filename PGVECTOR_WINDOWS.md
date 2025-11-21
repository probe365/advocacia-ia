# pgvector Installation Guide for Windows

## Overview
You're installing **pgvector v0.8.1** on Windows PostgreSQL 18. This guide covers the complete process.

---

## Prerequisites

✅ **Already Done (from your terminal):**
- Downloaded pgvector v0.8.1
- Built with nmake

✅ **Required:**
- PostgreSQL 18 installed
- Visual C++ Build Tools (for nmake)
- git
- Administrator access

---

## Complete Installation Process

### Step 1: Verify Your Build

The commands you already ran:

```batch
set "PGROOT=C:\Program Files\PostgreSQL\18"
cd %TEMP%
git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

This should have created:
- `%PGROOT%\lib\vector.dll`
- `%PGROOT%\share\extension\vector.control`
- `%PGROOT%\share\extension\vector--0.8.1.sql`

**Verify the files exist:**

```batch
dir "%PGROOT%\lib\vector.dll"
dir "%PGROOT%\share\extension\vector.*"
```

If files exist → ✅ Build successful
If not → See [Troubleshooting](#troubleshooting)

---

### Step 2: Restart PostgreSQL Service

```batch
REM As Administrator:
net stop postgresql-x64-18
net start postgresql-x64-18
```

Or use Services GUI:
- Press `Win + R` → `services.msc`
- Find "postgresql-x64-18"
- Restart it

---

### Step 3: Enable pgvector in Your Database

**Option A: Using Python (Recommended)**

```bash
python init_pgvector_windows.py
```

This script will:
- ✅ Check PostgreSQL service status
- ✅ Verify vector.dll is installed
- ✅ Create your database
- ✅ Enable pgvector extension
- ✅ Create embeddings schema
- ✅ Test vector operations

**Option B: Using psql directly**

```bash
# Connect to postgres database
psql -U postgres -d postgres

# Create extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify
\dx vector
```

Expected output:
```
                          List of installed extensions
Name   | Version | Schema |          Description
--------+---------+--------+------------------------------
vector | 0.8.1   | public | open-source vector similarity
(1 row)
```

---

### Step 4: Verify Installation

```bash
# Test with Python
python init_pgvector_windows.py

# Test with psql
psql -U postgres -d advia -c "CREATE EXTENSION IF NOT EXISTS vector; SELECT version();"
```

---

## Vector Operations

### Create a vector column:

```sql
-- In your database
CREATE SCHEMA IF NOT EXISTS embeddings;

CREATE TABLE embeddings.documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster search
CREATE INDEX ON embeddings.documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

### Insert vectors:

```sql
INSERT INTO embeddings.documents (content, embedding) 
VALUES (
    'Your legal text here',
    '[0.1, 0.2, 0.3, ..., 1.5]'::vector
);
```

### Search similar documents:

```sql
-- Find 5 most similar documents
SELECT id, content, embedding <=> query_vec AS distance
FROM embeddings.documents
ORDER BY embedding <=> query_vec
LIMIT 5;

-- Example with actual vector
SELECT id, content, embedding <=> '[0.1, 0.2, 0.3, ..., 1.5]'::vector AS distance
FROM embeddings.documents
ORDER BY embedding <=> '[0.1, 0.2, 0.3, ..., 1.5]'::vector
LIMIT 5;
```

---

## Distance Metrics

pgvector supports three distance operators:

| Operator | Name | Best For |
|----------|------|----------|
| `<->` | L2 (Euclidean) | General purpose |
| `<=>` | Cosine | Text embeddings ⭐ |
| `<\|>` | Inner product | Normalized vectors |

**Recommended for legal text:** Cosine distance `<=>`

---

## Integration with Python

### Using psycopg2:

```python
import psycopg2
import numpy as np

conn = psycopg2.connect(
    host="localhost",
    database="advia",
    user="advuser",
    password="advpass"
)

cursor = conn.cursor()

# Insert embedding
embedding = np.random.rand(1536).tolist()
cursor.execute(
    """INSERT INTO embeddings.documents (content, embedding) 
       VALUES (%s, %s)""",
    ("Your legal text", str(embedding))
)
conn.commit()

# Search similar
query_embedding = np.random.rand(1536).tolist()
cursor.execute("""
    SELECT id, content, embedding <=> %s::vector AS distance
    FROM embeddings.documents
    ORDER BY embedding <=> %s::vector
    LIMIT 5
""", (str(query_embedding), str(query_embedding)))

results = cursor.fetchall()
for row in results:
    print(f"ID: {row[0]}, Distance: {row[2]:.4f}")

cursor.close()
conn.close()
```

### Using Flask + SQLAlchemy (Optional):

```python
# First install pgvector Python package:
# pip install pgvector

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, Session
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = {'schema': 'embeddings'}
    
    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)

# Usage
engine = create_engine('postgresql://advuser:advpass@localhost/advia')
session = Session(engine)

# Search similar
query_vector = [0.1, 0.2, 0.3, ...]  # Your embedding
results = session.query(Document).order_by(
    Document.embedding.cosine_distance(query_vector)
).limit(5).all()

for doc in results:
    print(f"Content: {doc.content}")
```

---

## Docker Usage

Your `docker-compose.yml` already uses pgvector image:

```bash
# Start Docker containers
docker-compose down
docker-compose up -d

# Verify pgvector in container
docker-compose exec db psql -U advuser -d advia -c "\dx vector"
```

---

## Troubleshooting

### ❌ "could not open extension control file"

**Cause:** vector.dll not installed or in wrong location

**Solution:**
```batch
# Verify files exist
dir "C:\Program Files\PostgreSQL\18\lib\vector.dll"
dir "C:\Program Files\PostgreSQL\18\share\extension\vector.control"

# If missing, rebuild:
nmake /F Makefile.win clean
nmake /F Makefile.win
nmake /F Makefile.win install
```

### ❌ "Permission denied" during install

**Solution:** Run Command Prompt as Administrator
- Right-click `cmd.exe` → "Run as administrator"

### ❌ "nmake not found"

**Solution:** Install Visual C++ Build Tools
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Or add to PATH if already installed

### ❌ PostgreSQL service won't start after pgvector

**Solution:**
```batch
REM Check PostgreSQL logs
cd "C:\Program Files\PostgreSQL\18\data"
type postgresql.log

REM If corrupt, rebuild:
NET STOP postgresql-x64-18
rmdir /s "C:\Program Files\PostgreSQL\18\data\pg_tblspc"
rmdir /s "C:\Program Files\PostgreSQL\18\data\pg_replslot"
NET START postgresql-x64-18
```

### ❌ Python script fails to connect

**Check:**
```python
# Verify connection details
from config import get_config
cfg = get_config()()
print(f"Host: {cfg.DB_HOST}")
print(f"Port: {cfg.DB_PORT}")
print(f"Database: {cfg.DB_NAME}")
print(f"User: {cfg.DB_USER}")
```

---

## Quick Reference Commands

```bash
# Check pgvector version
psql -U postgres -d advia -c "SELECT extversion FROM pg_extension WHERE extname='vector';"

# List all tables with vectors
psql -U postgres -d advia -c "SELECT * FROM information_schema.columns WHERE data_type LIKE '%vector%';"

# Test cosine distance
psql -U postgres -d advia -c "SELECT '[1,2,3]'::vector <=> '[1,2,3]'::vector;"

# Show vector operations
psql -U postgres -d advia -c "SELECT '[1,2,3]'::vector + '[1,2,3]'::vector;"

# Restart PostgreSQL (batch)
net stop postgresql-x64-18 && net start postgresql-x64-18
```

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `install_pgvector_windows.bat` | Windows batch installer |
| `init_pgvector_windows.py` | Python initialization (preferred) |
| `docker-compose.yml` | Docker config with pgvector image |
| `init-pgvector.sql` | Docker initialization script |

---

## Next Steps

1. ✅ **Run Python initializer:**
   ```bash
   python init_pgvector_windows.py
   ```

2. ✅ **Verify embeddings table:**
   ```bash
   psql -U advuser -d advia -c "\dt embeddings.*"
   ```

3. ✅ **Test vector operations:**
   ```bash
   psql -U advuser -d advia -c "SELECT '[1,2,3]'::vector <=> '[1,2,3]'::vector;"
   ```

4. ✅ **Start using pgvector** in your Flask app or data pipeline

---

## References

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [pgvector Windows Build](https://github.com/pgvector/pgvector#windows)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Vector Similarity Search](https://en.wikipedia.org/wiki/Similarity_search)
