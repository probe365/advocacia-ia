-- Initialize pgvector extension
-- This script runs automatically when the PostgreSQL container starts

CREATE EXTENSION IF NOT EXISTS vector;

-- Optional: Create a schema for embeddings
CREATE SCHEMA IF NOT EXISTS embeddings;

-- Optional: Grant privileges
GRANT ALL ON SCHEMA embeddings TO :"POSTGRES_USER";

-- Log that pgvector is initialized
SELECT version();
SELECT extname FROM pg_extension WHERE extname = 'vector';
