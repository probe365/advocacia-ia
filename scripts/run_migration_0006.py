#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script standalone para executar migration 0006 - Create partes_adversas table
Executa SQL direto no banco advocacia_ia
"""
import psycopg2
import os

# Configuração do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'advocacia_ia',
    'user': 'postgres',
    'password': 'postgres'
}

# SQL da migration 0006
SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS partes_adversas (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamentos
    id_processo VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    
    -- Tipo de parte
    tipo_parte VARCHAR(20) NOT NULL,
    
    -- Dados pessoais/empresariais
    nome_completo VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    rg VARCHAR(20),
    qualificacao TEXT,
    
    -- Endereço completo
    endereco_completo TEXT,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(9),
    
    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Advogado da parte adversa (opcional)
    advogado_nome VARCHAR(255),
    advogado_oab VARCHAR(50),
    
    -- Observações
    observacoes TEXT,
    
    -- Auditoria
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_partes_adversas_processo 
        FOREIGN KEY (id_processo) 
        REFERENCES processos(id_processo) 
        ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_partes_adversas_processo 
    ON partes_adversas(id_processo);
    
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tenant 
    ON partes_adversas(tenant_id);
    
CREATE INDEX IF NOT EXISTS idx_partes_adversas_cpf_cnpj 
    ON partes_adversas(cpf_cnpj);
    
CREATE INDEX IF NOT EXISTS idx_partes_adversas_nome 
    ON partes_adversas(nome_completo);
    
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tipo 
    ON partes_adversas(tipo_parte);
    
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tenant_processo 
    ON partes_adversas(tenant_id, id_processo);

-- Comentários
COMMENT ON TABLE partes_adversas IS 'Cadastro de partes adversas (autor, réu, terceiros) vinculadas a processos';
COMMENT ON COLUMN partes_adversas.tipo_parte IS 'Valores: autor, reu, terceiro_interessado, litisconsorte';
COMMENT ON COLUMN partes_adversas.cpf_cnpj IS 'CPF (XXX.XXX.XXX-XX) ou CNPJ (XX.XXX.XXX/XXXX-XX) com máscara';
"""

def main():
    print("=" * 80)
    print("MIGRATION 0006: Create partes_adversas table")
    print("=" * 80)
    print()
    
    try:
        # Conectar ao banco
        print(f"📡 Conectando ao banco {DB_CONFIG['database']}@{DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()
        
        # Verificar se tabela já existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'partes_adversas'
            )
        """)
        exists = cur.fetchone()[0]
        
        if exists:
            print("⚠️  Tabela 'partes_adversas' JÁ EXISTE!")
            print("   Nenhuma alteração necessária.")
            conn.close()
            return
        
        # Executar CREATE TABLE + índices
        print("🔨 Executando CREATE TABLE partes_adversas...")
        cur.execute(SQL_CREATE_TABLE)
        
        # Verificar criação
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'partes_adversas' 
            ORDER BY ordinal_position
        """)
        cols = cur.fetchall()
        
        # Commit
        conn.commit()
        
        print()
        print("✅ SUCESSO! Tabela 'partes_adversas' criada com sucesso!")
        print(f"   Total de colunas: {len(cols)}")
        print()
        print("📋 Colunas criadas:")
        for col, dtype in cols:
            print(f"   - {col:<25} {dtype}")
        
        # Verificar índices
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'partes_adversas'
        """)
        indexes = [r[0] for r in cur.fetchall()]
        
        print()
        print(f"🔍 Índices criados ({len(indexes)}):")
        for idx in indexes:
            print(f"   - {idx}")
        
        conn.close()
        print()
        print("=" * 80)
        print("Migration 0006 executada com sucesso! ✨")
        print("=" * 80)
        
    except Exception as e:
        print()
        print(f"❌ ERRO ao executar migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    main()
