-- Migration 0006: Create partes_adversas table
-- Execute com: psql -U postgres -d advocacia_ia -f create_partes_adversas.sql

-- Criar tabela
CREATE TABLE IF NOT EXISTS partes_adversas (
    id SERIAL PRIMARY KEY,
    id_processo VARCHAR(50) NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    tipo_parte VARCHAR(20) NOT NULL,
    nome_completo VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    rg VARCHAR(20),
    qualificacao TEXT,
    endereco_completo TEXT,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(9),
    telefone VARCHAR(20),
    email VARCHAR(255),
    advogado_nome VARCHAR(255),
    advogado_oab VARCHAR(50),
    observacoes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_partes_adversas_processo 
        FOREIGN KEY (id_processo) 
        REFERENCES processos(id_processo) 
        ON DELETE CASCADE
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_partes_adversas_processo ON partes_adversas(id_processo);
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tenant ON partes_adversas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_partes_adversas_cpf_cnpj ON partes_adversas(cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_partes_adversas_nome ON partes_adversas(nome_completo);
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tipo ON partes_adversas(tipo_parte);
CREATE INDEX IF NOT EXISTS idx_partes_adversas_tenant_processo ON partes_adversas(tenant_id, id_processo);

-- Comentários
COMMENT ON TABLE partes_adversas IS 'Cadastro de partes adversas vinculadas a processos';
COMMENT ON COLUMN partes_adversas.tipo_parte IS 'Valores: autor, reu, terceiro_interessado, litisconsorte';

\echo '✅ Tabela partes_adversas criada com sucesso!'
