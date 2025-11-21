# Diagrama ER - Projeto "Advocacia e IA"
## Template para Modelagem Completa do Banco de Dados

**Data:** 09/11/2025  
**Versão:** 1.0 (Template Base)  
**Objetivo:** Mapear todas as entidades, relacionamentos e constraints do sistema reformatado

---

## 📐 LEGENDA

### Notação Utilizada
```
┌─────────────────┐
│  TABELA         │  ← Entidade
├─────────────────┤
│ PK id           │  ← Primary Key
│ FK fk_id        │  ← Foreign Key
│    campo        │  ← Campo normal
│ UK campo_unico  │  ← Unique constraint
│ IDX campo_idx   │  ← Index
└─────────────────┘

Relacionamentos:
─────  1:1 (um para um)
═════  1:N (um para muitos)
─ ─ ─  0/1:N (opcional)
```

### Tipos de Dados PostgreSQL
- `SERIAL` / `BIGSERIAL` - Auto-incremento
- `VARCHAR(n)` - String com limite
- `TEXT` - String sem limite
- `INTEGER` / `BIGINT` - Números inteiros
- `DECIMAL(p,s)` - Números decimais precisos
- `BOOLEAN` - Verdadeiro/Falso
- `DATE` - Data
- `TIMESTAMP` - Data + Hora
- `JSONB` - JSON binário (indexável)
- `TEXT[]` - Array de strings

---

## 🗂️ ESTRUTURA ATUAL (Baseline)

### 1. Tabela: `escritorio`
**Descrição:** Dados do escritório de advocacia (singleton - apenas 1 registro)

```sql
CREATE TABLE escritorio (
    -- Chave primária
    id INTEGER PRIMARY KEY DEFAULT 1,
    
    -- Dados corporativos
    razao_social VARCHAR(255),
    nome_fantasia VARCHAR(255),
    cnpj VARCHAR(18) UNIQUE,
    
    -- Contato
    endereco_completo TEXT,
    telefones JSONB,                    -- Ex: ["(11) 1234-5678", "(11) 98765-4321"]
    email_contato VARCHAR(255),
    site VARCHAR(255),
    
    -- Estrutura
    responsaveis JSONB,                 -- Ex: [{"nome": "Dr. João", "oab": "OAB123"}]
    areas_atuacao JSONB,                -- Ex: {"civil": true, "trabalhista": true}
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraint para garantir apenas 1 registro
    CONSTRAINT single_escritorio CHECK (id = 1)
);
```

---

### 2. Tabela: `advogados`
**Descrição:** Cadastro de advogados do escritório

```sql
CREATE TABLE advogados (
    -- Chave primária
    oab VARCHAR(20) PRIMARY KEY,        -- Ex: "SP123456" ou "OAB/SP 123.456"
    
    -- Dados pessoais
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    
    -- Atuação
    area_atuacao VARCHAR(100),          -- Ex: "Civil", "Trabalhista", "Família"
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_advogados_nome ON advogados(nome);
```

---

### 3. Tabela: `usuarios`
**Descrição:** Usuários do sistema (login e autenticação)

```sql
CREATE TABLE usuarios (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Autenticação
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Dados pessoais
    nome_completo VARCHAR(255),
    
    -- Relacionamentos
    advogado_oab VARCHAR(20) REFERENCES advogados(oab),  -- Opcional: usuário pode ser advogado
    
    -- Multi-tenant
    tenant_id VARCHAR(50),              -- ⚠️ Preencher se multi-tenant habilitado
    
    -- Metadados
    data_criacao TIMESTAMP DEFAULT NOW(),
    ultimo_login TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_usuarios_tenant ON usuarios(tenant_id);
```

---

### 4. Tabela: `clientes`
**Descrição:** Cadastro de clientes (pessoas físicas ou jurídicas)

```sql
CREATE TABLE clientes (
    -- Chave primária
    id_cliente VARCHAR(50) PRIMARY KEY,  -- UUID gerado
    
    -- Tipo
    tipo_pessoa VARCHAR(10),             -- 'FISICA' | 'JURIDICA'
    
    -- Dados principais
    nome_completo VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(18),
    rg_ie VARCHAR(20),
    
    -- Dados complementares (PF)
    nacionalidade VARCHAR(50),
    estado_civil VARCHAR(20),
    profissao VARCHAR(100),
    
    -- Dados complementares (PJ)
    responsavel_pj VARCHAR(255),         -- Nome do representante legal
    
    -- Contato
    endereco_completo TEXT,
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Observações
    observacoes TEXT,
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    data_cadastro DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_clientes_nome ON clientes(nome_completo);
CREATE INDEX idx_clientes_cpf_cnpj ON clientes(cpf_cnpj);
CREATE INDEX idx_clientes_tenant ON clientes(tenant_id);
```

---

### 5. Tabela: `processos`
**Descrição:** Cadastro de processos jurídicos (casos)

```sql
CREATE TABLE processos (
    -- Chave primária
    id_processo VARCHAR(50) PRIMARY KEY, -- Ex: "caso_11b044bc"
    
    -- Relacionamentos
    id_cliente VARCHAR(50) NOT NULL REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    advogado_oab VARCHAR(20) REFERENCES advogados(oab),
    
    -- Identificação
    nome_caso VARCHAR(255) NOT NULL,
    numero_cnj VARCHAR(25) UNIQUE,       -- NNNNNNN-DD.AAAA.J.TR.OOOO
    
    -- Status
    status VARCHAR(50),                  -- Ex: "ATIVO", "ARQUIVADO", "CONCLUÍDO"
    tipo_parte VARCHAR(20),              -- 'autor' | 'reu' | 'terceiro' | 'reclamante' | 'reclamada'
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    data_inicio DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_processos_cliente ON processos(id_cliente);
CREATE INDEX idx_processos_numero_cnj ON processos(numero_cnj);
CREATE INDEX idx_processos_advogado ON processos(advogado_oab);
CREATE INDEX idx_processos_tenant ON processos(tenant_id);
```

---

### 6. Tabela: `chat_turns`
**Descrição:** Histórico de conversas do chat RAG por processo

```sql
CREATE TABLE chat_turns (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_processo VARCHAR(50) NOT NULL REFERENCES processos(id_processo) ON DELETE CASCADE,
    
    -- Mensagem
    role VARCHAR(20) NOT NULL,           -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_turns_processo ON chat_turns(id_processo);
CREATE INDEX idx_chat_turns_created ON chat_turns(created_at);
```

---

## 🆕 NOVAS ENTIDADES PROPOSTAS

### 7. Tabela: `partes_adversas` ⭐ NOVA
**Descrição:** Dados da parte contrária no processo (autor/réu oposto ao cliente)

```sql
CREATE TABLE partes_adversas (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_processo VARCHAR(50) NOT NULL REFERENCES processos(id_processo) ON DELETE CASCADE,
    
    -- ⚠️ DECISÃO NECESSÁRIA: 1:1 ou 1:N?
    -- Se 1:1 → Adicionar: UNIQUE(id_processo)
    -- Se 1:N → Permitir múltiplas partes adversas por processo
    
    -- Tipo de parte
    tipo_parte VARCHAR(20) NOT NULL,     -- 'autor' | 'reu' | 'terceiro_interessado' | 'reclamante' | 'reclamada'
    
    -- Dados pessoais
    nome_completo VARCHAR(255) NOT NULL,
    nacionalidade VARCHAR(50),
    profissao VARCHAR(100),
    estado_civil VARCHAR(20),
    cpf_cnpj VARCHAR(18),
    rg_ie VARCHAR(20),
    email VARCHAR(255),
    telefone VARCHAR(20),
    nome_mae VARCHAR(255),
    
    -- Endereço completo
    cep VARCHAR(9),
    estado VARCHAR(2),
    cidade VARCHAR(100),
    bairro VARCHAR(100),
    logradouro VARCHAR(255),
    numero VARCHAR(10),
    complemento VARCHAR(100),
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
    
    -- ⚠️ ADICIONAR CONSTRAINT SE 1:1:
    -- UNIQUE(id_processo)
);

CREATE INDEX idx_partes_adversas_processo ON partes_adversas(id_processo);
CREATE INDEX idx_partes_adversas_cpf ON partes_adversas(cpf_cnpj);
CREATE INDEX idx_partes_adversas_nome ON partes_adversas(nome_completo);
```

**⚠️ DECISÃO NECESSÁRIA (Q3.1.1):**
- [ ] 1:1 - Um processo tem UMA parte adversa
- [ ] 1:N - Um processo pode ter MÚLTIPLAS partes adversas

---

### 8. Tabela: `movimentacoes_processuais` ⭐ NOVA
**Descrição:** Histórico de movimentações e eventos do processo

```sql
CREATE TABLE movimentacoes_processuais (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_processo VARCHAR(50) NOT NULL REFERENCES processos(id_processo) ON DELETE CASCADE,
    
    -- Dados da movimentação
    data_movimentacao TIMESTAMP NOT NULL,
    tipo_movimentacao VARCHAR(100),      -- Ex: "Audiência", "Despacho", "Sentença", "Intimação"
    descricao TEXT,
    
    -- Origem
    origem VARCHAR(20) NOT NULL,         -- 'automatica' | 'manual' | 'robot_pje'
    usuario_responsavel INTEGER REFERENCES usuarios(id),
    
    -- Anexo (opcional)
    documento_anexo VARCHAR(255),        -- Path ou URL do documento
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movimentacoes_processo ON movimentacoes_processuais(id_processo);
CREATE INDEX idx_movimentacoes_data ON movimentacoes_processuais(data_movimentacao);
CREATE INDEX idx_movimentacoes_tipo ON movimentacoes_processuais(tipo_movimentacao);
```

---

### 9. Tabela: `movimentacoes_clientes` ⭐ NOVA (OPCIONAL)
**Descrição:** Histórico de interações e alterações no cadastro do cliente

```sql
-- ⚠️ DECISÃO NECESSÁRIA (Q5.3.1): Implementar separado ou unificar com movimentacoes_processuais?

CREATE TABLE movimentacoes_clientes (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_cliente VARCHAR(50) NOT NULL REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    
    -- Dados da movimentação
    data_movimentacao TIMESTAMP NOT NULL,
    tipo_movimentacao VARCHAR(100),      -- 'Contato', 'Reunião', 'Alteração Cadastral', 'Novo Processo'
    descricao TEXT,
    
    -- Responsável
    usuario_responsavel INTEGER REFERENCES usuarios(id),
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movimentacoes_clientes_cliente ON movimentacoes_clientes(id_cliente);
CREATE INDEX idx_movimentacoes_clientes_data ON movimentacoes_clientes(data_movimentacao);
```

---

### 10. Tabela: `agendamentos` ⭐ NOVA (OPCIONAL)
**Descrição:** Agenda de compromissos, audiências e prazos

```sql
-- ⚠️ DECISÃO NECESSÁRIA (Q5.4.1): Sistema COMPLETO ou BÁSICO?

CREATE TABLE agendamentos (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamentos
    id_cliente VARCHAR(50) REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    id_processo VARCHAR(50) REFERENCES processos(id_processo) ON DELETE SET NULL,
    advogado_responsavel VARCHAR(20) REFERENCES advogados(oab),
    
    -- Dados do evento
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_hora TIMESTAMP NOT NULL,
    duracao_minutos INTEGER DEFAULT 60,
    
    -- Classificação
    tipo_evento VARCHAR(50),             -- 'Reunião', 'Audiência', 'Prazo', 'Ligação'
    local VARCHAR(255),
    
    -- Status
    status VARCHAR(20) DEFAULT 'agendado', -- 'agendado', 'concluido', 'cancelado', 'reagendado'
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agendamentos_cliente ON agendamentos(id_cliente);
CREATE INDEX idx_agendamentos_processo ON agendamentos(id_processo);
CREATE INDEX idx_agendamentos_data ON agendamentos(data_hora);
CREATE INDEX idx_agendamentos_advogado ON agendamentos(advogado_responsavel);
```

---

### 11. Tabela: `cliente_documentos` ⭐ NOVA
**Descrição:** Documentos anexados ao cliente/processo (para controle e RAG)

```sql
CREATE TABLE cliente_documentos (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamentos
    id_cliente VARCHAR(50) NOT NULL REFERENCES clientes(id_cliente) ON DELETE CASCADE,
    id_processo VARCHAR(50) REFERENCES processos(id_processo) ON DELETE CASCADE,
    -- ⚠️ Se id_processo NULL → documento geral do cliente
    -- ⚠️ Se id_processo preenchido → documento específico do processo
    
    -- Dados do arquivo
    nome_arquivo VARCHAR(255) NOT NULL,
    path_arquivo TEXT NOT NULL,          -- Path relativo ou absoluto
    tipo_documento VARCHAR(50),          -- 'RG', 'CPF', 'Contrato', 'Petição', 'Sentença', 'Certidão'
    tamanho_bytes BIGINT,
    mime_type VARCHAR(100),              -- 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    -- RAG
    indexado_rag BOOLEAN DEFAULT FALSE,  -- Se foi processado e adicionado ao vector store
    chroma_ids TEXT[],                   -- IDs dos chunks no Chroma (opcional)
    
    -- Upload
    usuario_upload INTEGER REFERENCES usuarios(id),
    data_upload TIMESTAMP DEFAULT NOW(),
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cliente_documentos_cliente ON cliente_documentos(id_cliente);
CREATE INDEX idx_cliente_documentos_processo ON cliente_documentos(id_processo);
CREATE INDEX idx_cliente_documentos_tipo ON cliente_documentos(tipo_documento);
CREATE INDEX idx_cliente_documentos_indexado ON cliente_documentos(indexado_rag);
```

---

### 12. Tabela: `comunicacoes_processuais` ⭐ NOVA
**Descrição:** Comunicações e intimações baixadas pelo Robot PJe

```sql
CREATE TABLE comunicacoes_processuais (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_processo VARCHAR(50) NOT NULL REFERENCES processos(id_processo) ON DELETE CASCADE,
    
    -- Dados da comunicação
    data_comunicacao TIMESTAMP NOT NULL,
    tipo_comunicacao VARCHAR(100),       -- 'Despacho', 'Intimação', 'Decisão', 'Sentença', 'Acórdão'
    conteudo_texto TEXT,                 -- Conteúdo extraído do documento
    
    -- Arquivo
    path_arquivo_pdf TEXT,               -- Path do PDF baixado
    hash_arquivo VARCHAR(64),            -- SHA-256 para detectar duplicatas
    
    -- Origem
    origem VARCHAR(20) DEFAULT 'robot_pje', -- 'robot_pje', 'manual', 'api_datajud'
    
    -- RAG
    indexado_rag BOOLEAN DEFAULT FALSE,
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comunicacoes_processo ON comunicacoes_processuais(id_processo);
CREATE INDEX idx_comunicacoes_data ON comunicacoes_processuais(data_comunicacao);
CREATE INDEX idx_comunicacoes_tipo ON comunicacoes_processuais(tipo_comunicacao);
CREATE UNIQUE INDEX idx_comunicacoes_hash ON comunicacoes_processuais(hash_arquivo); -- Evita duplicatas
```

---

### 13. Tabela: `analises_processos` ⭐ NOVA (OPCIONAL)
**Descrição:** Análises geradas pela IA (FIRAC, resumos, estratégias) - persistência no BD

```sql
-- ⚠️ DECISÃO NECESSÁRIA (Q6.2.1): Migrar de cache de arquivos para BD?

CREATE TABLE analises_processos (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Relacionamento
    id_processo VARCHAR(50) NOT NULL REFERENCES processos(id_processo) ON DELETE CASCADE,
    
    -- Tipo de análise
    tipo_analise VARCHAR(50) NOT NULL,   -- 'resumo', 'estrategia', 'firac', 'riscos', 'sugestoes'
    
    -- Conteúdo
    conteudo_json JSONB NOT NULL,        -- Estrutura JSON com os dados da análise
    conteudo_texto TEXT,                 -- Versão em texto puro (para busca)
    
    -- Versionamento
    versao INTEGER DEFAULT 1,            -- Permite histórico de versões
    
    -- Multi-tenant
    tenant_id VARCHAR(50),
    
    -- Metadados
    data_geracao TIMESTAMP DEFAULT NOW(),
    usuario_solicitante INTEGER REFERENCES usuarios(id)
);

CREATE INDEX idx_analises_processo ON analises_processos(id_processo);
CREATE INDEX idx_analises_tipo ON analises_processos(tipo_analise);
CREATE INDEX idx_analises_data ON analises_processos(data_geracao);

-- Exemplo de consulta de histórico:
-- SELECT * FROM analises_processos 
-- WHERE id_processo = 'caso_123' AND tipo_analise = 'firac' 
-- ORDER BY versao DESC;
```

---

### 14. Tabela: `kb_global_documentos` ⭐ NOVA
**Descrição:** Documentos da Knowledge Base Global (leis, jurisprudências, doutrinas)

```sql
CREATE TABLE kb_global_documentos (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Dados do documento
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    path_arquivo TEXT NOT NULL,
    
    -- Classificação
    categoria VARCHAR(100),              -- 'Civil', 'Trabalhista', 'Penal', etc.
    tags TEXT[],                         -- Ex: ['CLT', 'Acidente de Trabalho', 'Indenização']
    tipo_documento VARCHAR(50),          -- 'Jurisprudência', 'Doutrina', 'Legislação', 'Modelo de Petição'
    
    -- Arquivo
    tamanho_bytes BIGINT,
    mime_type VARCHAR(100),
    
    -- RAG
    indexado_rag BOOLEAN DEFAULT FALSE,
    chroma_ids TEXT[],
    
    -- Upload
    usuario_upload INTEGER REFERENCES usuarios(id),
    data_upload TIMESTAMP DEFAULT NOW(),
    
    -- Multi-tenant (⚠️ KB pode ser compartilhada ou privada por tenant)
    tenant_id VARCHAR(50),               -- NULL = compartilhado entre todos
    visibilidade VARCHAR(20) DEFAULT 'privado', -- 'privado', 'publico', 'compartilhado'
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kb_global_categoria ON kb_global_documentos(categoria);
CREATE INDEX idx_kb_global_tags ON kb_global_documentos USING GIN(tags);
CREATE INDEX idx_kb_global_tipo ON kb_global_documentos(tipo_documento);
CREATE INDEX idx_kb_global_tenant ON kb_global_documentos(tenant_id);
```

---

### 15. Tabela: `tenants` ⭐ NOVA (SAAS)
**Descrição:** Controle de escritórios (multi-tenant SaaS)

```sql
-- ⚠️ DECISÃO NECESSÁRIA (Q10.3.1): Implementar agora ou em versão futura?

CREATE TABLE tenants (
    -- Chave primária
    tenant_id VARCHAR(50) PRIMARY KEY,   -- Ex: "escritorio_silva_advogados"
    
    -- Dados do escritório
    nome_escritorio VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    email_admin VARCHAR(255) NOT NULL,
    telefone_contato VARCHAR(20),
    
    -- Plano e limites
    plano VARCHAR(20) DEFAULT 'basico',  -- 'basico', 'profissional', 'enterprise'
    status VARCHAR(20) DEFAULT 'ativo',  -- 'ativo', 'suspenso', 'cancelado', 'trial'
    
    -- Quotas
    limite_usuarios INTEGER DEFAULT 5,
    limite_processos INTEGER DEFAULT 100,
    limite_storage_gb INTEGER DEFAULT 10,
    
    -- Billing
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_expiracao DATE,                 -- NULL = sem expiração
    ultimo_pagamento DATE,
    proximo_vencimento DATE,
    valor_mensal DECIMAL(10,2),
    
    -- Customizações
    configuracoes JSONB,                 -- Ex: {"logo_url": "...", "cor_primaria": "#123456"}
    
    -- Metadados
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plano ON tenants(plano);
CREATE INDEX idx_tenants_cnpj ON tenants(cnpj);
```

---

## ⚙️ CAMPOS ADICIONAIS NAS TABELAS EXISTENTES

### Alterações na Tabela `processos`

**⚠️ NOVOS CAMPOS PROPOSTOS (Q1.2.1):**

```sql
-- ==========================================
-- ADICIONAR CAMPOS À TABELA processos
-- ==========================================

ALTER TABLE processos 
    -- Campos de tramitação
    ADD COLUMN local_tramite TEXT,                    -- Ex: "1ª Vara Cível"
    ADD COLUMN status_processual VARCHAR(50),         -- Ex: "Em andamento", "Suspenso"
    ADD COLUMN comarca VARCHAR(100),                  -- Ex: "São Paulo"
    ADD COLUMN area_atuacao VARCHAR(50),              -- 'Civil' | 'Trabalhista' | 'Penal' | 'Família'
    ADD COLUMN fase TEXT,                             -- Ex: "1ª Instância - Postulatória"
    
    -- Classificação
    ADD COLUMN objeto_acao TEXT,                      -- Ex: "Cobrança de honorários"
    ADD COLUMN assunto VARCHAR(255),                  -- Assunto processual
    ADD COLUMN responsavel INTEGER REFERENCES usuarios(id),
    
    -- Valores e datas
    ADD COLUMN valor_causa DECIMAL(15,2),             -- Ex: 50000.00
    ADD COLUMN data_distribuicao DATE,
    ADD COLUMN data_encerramento DATE,
    
    -- Sentença e execução
    ADD COLUMN sentenca TEXT,                         -- Texto completo ou resumo
    ADD COLUMN em_execucao BOOLEAN DEFAULT FALSE,
    
    -- Outros
    ADD COLUMN segredo_justica BOOLEAN DEFAULT FALSE;

-- Criar índices para performance
CREATE INDEX idx_processos_comarca ON processos(comarca);
CREATE INDEX idx_processos_area ON processos(area_atuacao);
CREATE INDEX idx_processos_fase ON processos(fase);
CREATE INDEX idx_processos_segredo ON processos(segredo_justica) WHERE segredo_justica = TRUE;
```

---

### Alterações na Tabela `clientes`

**⚠️ NOVOS CAMPOS PROPOSTOS (Q5.1.1):**

```sql
-- ==========================================
-- ADICIONAR CAMPOS À TABELA clientes
-- ==========================================

ALTER TABLE clientes
    -- Endereço estruturado (separar de endereco_completo)
    ADD COLUMN cep VARCHAR(9),
    ADD COLUMN estado VARCHAR(2),
    ADD COLUMN cidade VARCHAR(100),
    ADD COLUMN bairro VARCHAR(100),
    ADD COLUMN logradouro VARCHAR(255),
    ADD COLUMN numero VARCHAR(10),
    ADD COLUMN complemento VARCHAR(100),
    
    -- Dados adicionais PF
    ADD COLUMN nome_mae VARCHAR(255);

-- Criar índices
CREATE INDEX idx_clientes_estado ON clientes(estado);
CREATE INDEX idx_clientes_cidade ON clientes(cidade);
CREATE INDEX idx_clientes_cep ON clientes(cep);
```

---

## 📊 DIAGRAMA DE RELACIONAMENTOS

### Relacionamentos Principais

```
┌─────────────────┐
│   escritorio    │  (Singleton)
└─────────────────┘


┌─────────────────┐         ┌─────────────────┐
│   advogados     │────1:N──│    usuarios     │
│  (PK: oab)      │         │  (FK: advogado) │
└─────────────────┘         └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐         ┌─────────────────┐
│   processos     │═══1:N═══│    clientes     │
│                 │         │                 │
└─────────────────┘         └─────────────────┘
         ║                           ║
         ║ 1:N                       ║ 1:N
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ partes_adversas  │        │movimentacoes_    │
│                  │        │   clientes       │
└──────────────────┘        └──────────────────┘
         │
         │
         ▼
┌──────────────────────────────────────────────┐
│            processos (hub central)           │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │ Relacionamentos 1:N                │     │
│  ├────────────────────────────────────┤     │
│  │ • movimentacoes_processuais        │     │
│  │ • comunicacoes_processuais         │     │
│  │ • cliente_documentos (com FK)      │     │
│  │ • analises_processos               │     │
│  │ • agendamentos (com FK)            │     │
│  │ • chat_turns                       │     │
│  └────────────────────────────────────┘     │
└──────────────────────────────────────────────┘


┌─────────────────┐
│    tenants      │  ← Multi-tenant (SaaS)
│                 │    Todas tabelas com tenant_id referenciam esta
└─────────────────┘


┌───────────────────┐
│ kb_global_docs    │  ← Knowledge Base Global (compartilhada ou por tenant)
└───────────────────┘
```

---

## 🔐 CONSTRAINTS E REGRAS DE NEGÓCIO

### 1. Imutabilidade do Número CNJ (Item 2)

```sql
-- Trigger para prevenir alteração do numero_cnj após definição
CREATE OR REPLACE FUNCTION prevent_cnj_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.numero_cnj IS NOT NULL AND NEW.numero_cnj != OLD.numero_cnj THEN
        RAISE EXCEPTION 'Número CNJ não pode ser alterado após definição';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_cnj_update
BEFORE UPDATE ON processos
FOR EACH ROW
EXECUTE FUNCTION prevent_cnj_update();
```

---

### 2. Validação de Formato do Número CNJ

```sql
-- Constraint para validar formato: NNNNNNN-DD.AAAA.J.TR.OOOO
ALTER TABLE processos
ADD CONSTRAINT check_cnj_format
CHECK (
    numero_cnj IS NULL OR
    numero_cnj ~ '^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
);
```

---

### 3. Relacionamento Cliente ↔ Processo (Cascade Delete)

```sql
-- Se cliente for deletado, processos devem ser:
-- OPÇÃO A: Deletados também (CASCADE) ⚠️ PERIGOSO
-- OPÇÃO B: Impedidos (RESTRICT)
-- OPÇÃO C: Cliente marcado como inativo (soft delete)

-- Atualmente: ON DELETE CASCADE
-- Considerar mudar para RESTRICT ou implementar soft delete
```

---

### 4. Multi-Tenant Row Level Security (RLS)

```sql
-- ⚠️ IMPLEMENTAR SE SAAS COM ALTO NÍVEL DE SEGURANÇA

-- Habilitar RLS
ALTER TABLE processos ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
-- ... (repetir para todas tabelas com tenant_id)

-- Política: usuário só vê dados do próprio tenant
CREATE POLICY tenant_isolation_policy ON processos
USING (tenant_id = current_setting('app.current_tenant')::text);

-- Aplicação deve definir: SET app.current_tenant = 'escritorio_123';
```

---

## 📈 ÍNDICES PARA PERFORMANCE

### Índices Compostos Sugeridos

```sql
-- Busca de processos por cliente + status
CREATE INDEX idx_processos_cliente_status 
ON processos(id_cliente, status);

-- Busca de processos por advogado + área
CREATE INDEX idx_processos_advogado_area 
ON processos(advogado_oab, area_atuacao);

-- Movimentações recentes
CREATE INDEX idx_movimentacoes_processo_data 
ON movimentacoes_processuais(id_processo, data_movimentacao DESC);

-- Comunicações não indexadas no RAG
CREATE INDEX idx_comunicacoes_nao_indexadas 
ON comunicacoes_processuais(indexado_rag) 
WHERE indexado_rag = FALSE;

-- Documentos por cliente e processo
CREATE INDEX idx_documentos_cliente_processo 
ON cliente_documentos(id_cliente, id_processo);
```

---

## 🎯 CHECKLIST DE VALIDAÇÃO

Antes de implementar, validar:

- [ ] **Relacionamentos 1:1 vs 1:N definidos** (ex: partes_adversas)
- [ ] **Campos obrigatórios identificados** (NOT NULL)
- [ ] **Tipos de dados adequados** (VARCHAR vs TEXT, INTEGER vs BIGINT)
- [ ] **Índices criados para queries frequentes**
- [ ] **Foreign Keys com ações ON DELETE definidas** (CASCADE, RESTRICT, SET NULL)
- [ ] **Constraints de validação** (CHECK, UNIQUE)
- [ ] **Campos de auditoria** (created_at, updated_at, usuario_responsavel)
- [ ] **Suporte multi-tenant** (tenant_id em todas tabelas relevantes)
- [ ] **Triggers para regras de negócio** (ex: imutabilidade CNJ)
- [ ] **Campos de soft delete se necessário** (deleted_at, ativo)
- [ ] **JSONB para dados flexíveis** (configuracoes, metadados)
- [ ] **Arrays PostgreSQL** (tags, chroma_ids) onde apropriado

---

## 📝 PRÓXIMOS PASSOS

1. **Preencher o Questionário Técnico** (`QUESTIONARIO_TECNICO_REFORMATACAO.md`)
2. **Validar este template** com equipe e Dr. Kelety
3. **Ajustar estruturas** baseado nas respostas do questionário
4. **Criar migrations Alembic** para cada nova tabela/campo
5. **Atualizar models.py** com SQLAlchemy/Pydantic
6. **Implementar endpoints Flask** para CRUD das novas entidades
7. **Criar interface frontend** (formulários, listagens)
8. **Testes de integração** e validação com dados reais

---

## 🔗 FERRAMENTAS ÚTEIS

### Visualização de Diagramas ER

- **dbdiagram.io** - https://dbdiagram.io/
  - Syntax simples, gera imagem PNG
  - Exemplo:
    ```
    Table processos {
      id_processo varchar [pk]
      id_cliente varchar [ref: > clientes.id_cliente]
      numero_cnj varchar [unique]
    }
    ```

- **draw.io** - https://app.diagrams.net/
  - Editor visual drag-and-drop

- **DBeaver** - Cliente SQL com geração automática de ER
  - Conectar no PostgreSQL existente
  - Tools → ER Diagram

- **pgAdmin** - ER Diagram integrado

---

**Documento gerado em 09/11/2025 para o projeto "Advocacia e IA"**  
**Versão do Template:** 1.0  
**Próxima Revisão:** Após preenchimento do Questionário Técnico
