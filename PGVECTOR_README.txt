# pgvector Installation - Windows Summary

## Your Current Status ✅

You have successfully built pgvector v0.8.1 from source using nmake on Windows PostgreSQL 18.

### Build Output
```
nmake /F Makefile.win
nmake /F Makefile.win install
```

This created:
- ✅ `C:\Program Files\PostgreSQL\18\lib\vector.dll`
- ✅ `C:\Program Files\PostgreSQL\18\share\extension\vector.*`

---

## Complete Setup in 3 Steps

### Step 1: Restart PostgreSQL Service (Required)

**As Administrator:**
```batch
net stop postgresql-x64-18
net start postgresql-x64-18
```

Or using Windows Services:
- Press `Win + R` → type `services.msc`
- Find "postgresql-x64-18"
- Right-click → Restart

---

### Step 2: Initialize pgvector Extension

**Option A - Recommended (Python):**
```bash
python init_pgvector_windows.py
```

**Option B - Quick batch script:**
```bash
setup_pgvector_quick.bat
```

**Option C - Manual (psql):**
```bash
psql -U postgres -d postgres
CREATE EXTENSION IF NOT EXISTS vector;
\dx vector
```

---

### Step 3: Verify Installation

```bash
# Using Python initializer
python init_pgvector_windows.py

# Or manually with psql
psql -U advuser -d advia -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
```

Expected output: `0.8.1`

---

## Files We Created

| File | Purpose | Run With |
|------|---------|----------|
| `init_pgvector_windows.py` | **Recommended** - Auto-initialize pgvector | `python init_pgvector_windows.py` |
| `setup_pgvector_quick.bat` | Quick setup with PostgreSQL restart | Run as Administrator |
| `install_pgvector_windows.bat` | Full installation from scratch | Run as Administrator |
| `PGVECTOR_WINDOWS.md` | Complete documentation | Reference |
| `init-pgvector.sql` | Docker initialization script | Auto-runs in Docker |
| `docker-compose.yml` | Docker config (already pgvector-ready) | `docker-compose up -d` |

---

## Quick Commands

### Enable pgvector (first time)
```bash
python init_pgvector_windows.py
```

### Check pgvector status
```bash
psql -U advuser -d advia -c "\dx vector"
```

### Test vector operations
```bash
psql -U advuser -d advia -c "SELECT '[1,2,3]'::vector;"
```

### Create embeddings table
```bash
psql -U advuser -d advia << EOF
CREATE SCHEMA IF NOT EXISTS embeddings;

CREATE TABLE embeddings.documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_embedding 
ON embeddings.documents USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
EOF
```

### Search similar embeddings
```sql
SELECT id, content, embedding <=> query_vec AS distance
FROM embeddings.documents
ORDER BY embedding <=> query_vec
LIMIT 5;
```

---

## Python Usage Example

```python
import psycopg2
import numpy as np

# Connect
conn = psycopg2.connect(
    host="localhost",
    database="advia",
    user="advuser",
    password="advpass"
)
cursor = conn.cursor()

# Insert with embedding
embedding = np.random.rand(1536).tolist()
cursor.execute(
    "INSERT INTO embeddings.documents (content, embedding) VALUES (%s, %s)",
    ("Your legal text", str(embedding))
)
conn.commit()

# Search similar
query_vec = np.random.rand(1536).tolist()
cursor.execute("""
    SELECT id, content, embedding <=> %s::vector AS distance
    FROM embeddings.documents
    ORDER BY embedding <=> %s::vector
    LIMIT 5
""", (str(query_vec), str(query_vec)))

for row in cursor.fetchall():
    print(f"ID: {row[0]}, Distance: {row[2]:.4f}")

cursor.close()
conn.close()
```

---

## Troubleshooting

### PostgreSQL service won't start
```batch
# Check logs
type "C:\Program Files\PostgreSQL\18\data\postgresql.log"

# Restart service
net stop postgresql-x64-18
net start postgresql-x64-18
```

### Extension not found
```bash
# Verify files exist
dir "C:\Program Files\PostgreSQL\18\lib\vector.dll"
dir "C:\Program Files\PostgreSQL\18\share\extension\vector.control"

# If missing, rebuild:
cd %TEMP%\pgvector
nmake /F Makefile.win clean
nmake /F Makefile.win
nmake /F Makefile.win install
```

### Connection fails from Python
```python
# Test connection
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        database="advia",
        user="advuser",
        password="advpass",
        connect_timeout=5
    )
    print("✅ Connection successful")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

---

## What's Next?

1. ✅ **Run initializer:**
   ```bash
   python init_pgvector_windows.py
   ```

2. ✅ **Create embeddings table** (see SQL above)

3. ✅ **Use in your Flask app:**
   ```python
   # In your route handler
   from your_embeddings_module import get_similar_documents
   
   @app.route("/api/search_similar", methods=["POST"])
   def search_similar():
       query = request.json.get("query")
       results = get_similar_documents(query, k=10)
       return jsonify(results)
   ```

4. ✅ **Generate embeddings** using your LLM pipeline

---

## Documentation Files

- **`PGVECTOR_WINDOWS.md`** - Complete setup guide with examples
- **`PGVECTOR_SETUP.md`** - Cross-platform reference
- **`init_pgvector_windows.py`** - Detailed initialization code

---

## Ready! 🚀

Your pgvector installation is complete. Start with:

```bash
python init_pgvector_windows.py
```

Then begin creating and querying vector embeddings in your legal case management system!
