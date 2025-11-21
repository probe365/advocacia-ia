-- Migration 0005: Add 12 new fields to processos table
-- Execute com: psql -U postgres -d advocacia_ia -f add_processos_fields.sql

-- Adicionar 12 novos campos
ALTER TABLE processos ADD COLUMN IF NOT EXISTS local_tramite TEXT;
ALTER TABLE processos ADD COLUMN IF NOT EXISTS comarca VARCHAR(100);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS area_atuacao VARCHAR(50);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS instancia VARCHAR(20);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS subfase VARCHAR(50);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS assunto VARCHAR(255);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS valor_causa DECIMAL(15,2);
ALTER TABLE processos ADD COLUMN IF NOT EXISTS data_distribuicao DATE;
ALTER TABLE processos ADD COLUMN IF NOT EXISTS data_encerramento DATE;
ALTER TABLE processos ADD COLUMN IF NOT EXISTS sentenca TEXT;
ALTER TABLE processos ADD COLUMN IF NOT EXISTS em_execucao BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE processos ADD COLUMN IF NOT EXISTS segredo_justica BOOLEAN DEFAULT FALSE NOT NULL;

-- Comentários
COMMENT ON COLUMN processos.local_tramite IS 'Localização atual do processo (Vara, Tribunal, Cartório)';
COMMENT ON COLUMN processos.comarca IS 'Comarca onde o processo tramita';
COMMENT ON COLUMN processos.area_atuacao IS 'Área jurídica: Civil, Trabalhista, Penal, Tributário, etc';
COMMENT ON COLUMN processos.instancia IS '1ª Instância, 2ª Instância, Tribunais Superiores';
COMMENT ON COLUMN processos.subfase IS 'Fase processual: Inicial, Instrução, Sentenciado, Recursal, Execução';
COMMENT ON COLUMN processos.assunto IS 'Assunto principal do processo';
COMMENT ON COLUMN processos.valor_causa IS 'Valor econômico da causa em reais';
COMMENT ON COLUMN processos.data_distribuicao IS 'Data de distribuição do processo';
COMMENT ON COLUMN processos.data_encerramento IS 'Data de encerramento do processo';
COMMENT ON COLUMN processos.sentenca IS 'Texto completo da sentença (se houver)';
COMMENT ON COLUMN processos.em_execucao IS 'Indica se o processo está em fase de execução';
COMMENT ON COLUMN processos.segredo_justica IS 'Indica se o processo corre em segredo de justiça';

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_processos_area_atuacao ON processos(area_atuacao);
CREATE INDEX IF NOT EXISTS idx_processos_instancia ON processos(instancia);
CREATE INDEX IF NOT EXISTS idx_processos_comarca ON processos(comarca);

\echo '✅ 12 novos campos adicionados à tabela processos com sucesso!'
