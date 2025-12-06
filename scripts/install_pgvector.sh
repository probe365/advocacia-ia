#!/bin/bash
# Install pgvector on Ubuntu/Debian
# Run with: bash install_pgvector.sh

set -e

echo "Installing pgvector dependencies..."
sudo apt-get update
sudo apt-get install -y \
    postgresql-contrib \
    postgresql-server-dev-16 \
    build-essential \
    git

echo "Cloning pgvector repository..."
cd /tmp
git clone --branch v0.6.0 https://github.com/pgvector/pgvector.git
cd pgvector

echo "Building pgvector..."
make
sudo make install

echo "Creating pgvector extension in PostgreSQL..."
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ pgvector installed successfully!"
echo "Verify with: psql -U postgres -c '\\dx vector'"
