# Questionário Técnico - Reformatação do Projeto "Advocacia e IA"

**Data:** 09/11/2025  
**Objetivo:** Esclarecer requisitos e especificações técnicas para implementação das 10 alterações programadas  
**Status do Projeto:** Análise de viabilidade e planejamento

---

## 📋 INSTRUCÕES DE PREENCHIMENTO

Para cada seção abaixo:
1. ✅ **Responda todas as perguntas marcadas como [OBRIGATÓRIO]**
2. ⚠️ **Responda perguntas [RECOMENDADO] sempre que possível**
3. ℹ️ **Perguntas [OPCIONAL] ajudam no planejamento detalhado**
4. Use exemplos concretos quando solicitado
5. Anexe diagramas, templates ou mockups quando disponíveis

---

## 1️⃣ ITEM 1 - CADASTRO DE PROCESSOS E NÚMERO CNJ

### 1.1 Estrutura do Número CNJ
**Status:** ✅ **BEM DEFINIDO** (formatação NNNNNNN-DD.AAAA.J.TR.OOOO)

**[OBRIGATÓRIO] Q1.1.1:** O sistema deve validar o dígito verificador (DD) matematicamente?
- [ ] Sim, implementar algoritmo de validação
- [ ] Não, apenas validação de formato (20 dígitos)
- [X] Futuramente (versão 2.0)

**[RECOMENDADO] Q1.1.2:** Como tratar números CNJ inválidos em importações CSV?
- [ ] Rejeitar linha e registrar erro
- [X] Aceitar mas marcar como "não validado"
- [ ] Solicitar confirmação manual
- [ ] Outro: _______________

---

### 1.2 Novos Campos do Cadastro de Processos

**Campos Atuais no BD:**
- `id_processo` (PK)
- `id_cliente` (FK)
- `nome_caso`
- `numero_cnj`
- `status`
- `data_inicio`
- `advogado_oab` (FK)
- `tipo_parte` (autor/reu/terceiro/reclamante/reclamada)
- `tenant_id`

**[OBRIGATÓRIO] Q1.2.1:** Especifique os **novos campos** a serem adicionados:

| Campo Proposto | Tipo de Dado | Obrigatório? | Valores Possíveis | Observações |
|----------------|--------------|--------------|-------------------|-------------|
| `local_tramite` | **TEXT** /  | X Sim ☐ Não | Ex: "**1ª Vara Cível**" | Se FK, para qual tabela? |
| `status_processual` | ENUM / **TEXT** | X Sim ☐ Não | Mesmo que **tipo_parte** | **tipo_parte** |
| `comarca` | **TEXT** /  | X Sim ☐ Não | **Ex: "São Paulo"** | **Extrair do CNJ** ou campo livre? |
| `area_atuacao` | ENUM | X Sim ☐ Não | **☐ Civil ☐ Trabalhista ☐ Penal ☐ Família ☐ Outro** | Adicionar mais áreas? |
| `fase` | **TEXT** /  | ☐ Sim ☐ Não | Ex: "Postulatória", "Instrutória" | Ver Q1.2.2 |
| `objeto_acao` | TEXT | X Sim ☐ Não | Ex: "Cobrança de honorários" | É o mesmo que `nome_caso`? **SIM**|
| `responsavel` | FK / TEXT | X Sim ☐ Não | FK → `advogados` ou `usuarios`? | Diferente de `advogado_oab`? **É O MESMO QUE ADVOGADO_OAB** |
| `assunto` | TEXT / FK | ☐ Sim ☐ Não | Texto livre ou tabela CNJ? | **Ver Q1.2.3** |
| `valor_causa` | DECIMAL | X Sim ☐ Não | Ex: 50000.00 | Formato BRL |
| `data_encerramento` | DATE | ☐ Sim ☐ Não | **NULL se em andamento** | |
| `sentenca` | TEXT / JSON | ☐ Sim ☐ Não | Texto completo ou resumo? | Ver Q1.2.4 |
| `data_distribuicao` | DATE | X Sim ☐ Não | **Data de protocolo** | |
| `em_execucao` | **BOOLEAN** | X Sim ☐ Não | TRUE/FALSE | Ou tabela separada? Ver Q1.2.5 |
| `segredo_justica` | **BOOLEAN** | X Sim ☐ Não | TRUE/FALSE | Impacta visualização? |

**[OBRIGATÓRIO] Q1.2.2:** Campo `fase` - estrutura hierárquica:
- **Opção A:** Campo único TEXT (ex: "1ª Instância - Postulatória")
- **Opção B:** Dois campos separados: `instancia` (1ª/2ª) + `subfase` (Postulatória/Saneadora/...) **SOMENTE 1a. INSTÂNCIA TEM FASES (Postulatória, Saneadora, ..). APÓS FASE DECISÓRIA PODE IR OU NÃO PARA 2a. INSTÂNCIA.**
- **Opção C:** Tabela `fases_processuais` com hierarquia (FK)
- **Escolha:** ☐ A X B ☐ C

**[RECOMENDADO] Q1.2.3:** Campo `assunto`:
- **Opção A:** Texto livre (input text)
- **Opção B:** Tabela de assuntos pré-cadastrados (select dropdown)
- **Opção C:** Tabela oficial do CNJ (API ou import estático)
- **Escolha:** ☐ A X B ☐ C
- **Se B ou C:** Fornecer lista/link dos assuntos ==> DANOS MATERIAIS / DANOS MORAL / DANOS MATERIAIS E MORAL

**[RECOMENDADO] Q1.2.4:** Campo `sentenca`:
```
☐ Texto completo (até 50.000 caracteres)
**X Resumo executivo (até 2.000 caracteres)**
☐ Arquivo PDF anexo (path/URL)
☐ JSON estruturado: {tipo: "procedente", data: "...", resumo: "..."}
☐ Outro: _______________
```

**[RECOMENDADO] Q1.2.5:** Campo `em_execucao`:
```
X Boolean simples na tabela processos
☐ Tabela separada execucoes_processuais (1:1):
   - id_processo (FK)
   - data_inicio_execucao
   - fase_execucao (penhora/leilão/pagamento)
   - valor_executado
   - observacoes
☐ Outro: _______________
```

---

### 1.3 Ficha de Movimentações do Processo

**[OBRIGATÓRIO] Q1.3.1:** Estrutura da tabela `movimentacoes_processuais`:

```sql
CREATE TABLE movimentacoes_processuais (
    id SERIAL PRIMARY KEY,
    id_processo VARCHAR(50) REFERENCES processos(id_processo),
    data_movimentacao TIMESTAMP NOT NULL,
    tipo_movimentacao VARCHAR(100),  -- Ex: "Audiência", "Despacho", "Sentença"
    descricao TEXT,
    origem VARCHAR(20),  -- 'automatica' | 'manual' | 'robot_pje'
    usuario_responsavel INT REFERENCES usuarios(id),
    documento_anexo VARCHAR(255),  -- Path para arquivo
    tenant_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Essa estrutura está adequada?**
- [X] Sim, aprovar
- [ ] Não, ajustar: _______________

**[OBRIGATÓRIO] Q1.3.2:** Eventos que disparam registro automático:
- [X] Upload de documento no processo
- [X] Geração de petição
- [X] Alteração de status/fase
- [X] Dados do Robot PJe (comunicações processuais)
- [X] Agendamentos cumpridos
- [ ] Outros: _______________

**[RECOMENDADO] Q1.3.3:** Interface de visualização:
- [ ] Timeline cronológica (estilo Facebook)
- [ ] Tabela com filtros (data, tipo, usuário)
- [X] Ambas
- [ ] Outro: _______________

---

## 2️⃣ ITEM 2 - IMUTABILIDADE DO NÚMERO CNJ

**[OBRIGATÓRIO] Q2.1:** Regra de negócio:
```
Uma vez que o número CNJ é preenchido, ele NÃO pode ser alterado.
```
**Implementação:**
- [ ] Validação no backend (Flask route)
- [ ] Constraint no BD (trigger PostgreSQL)
- [X] Ambos
- [ ] Apenas UI (disabled input) ⚠️ NÃO RECOMENDADO

**[RECOMENDADO] Q2.2:** Exceções à regra:
- [X] Admin/Superusuário pode editar com log de auditoria
- [ ] Ninguém pode editar (nem admin)
- [ ] Permite correção dentro de 24h após criação
- [ ] Outro: _______________

---

## 3️⃣ ITEM 3 - CADASTRO DA PARTE ADVERSA

### 3.1 Estrutura da Tabela

**[OBRIGATÓRIO] Q3.1.1:** Relacionamento com `processos`:
- [ ] **1:1** - Um processo tem UMA parte adversa
- [X] **1:N** - Um processo pode ter MÚLTIPLAS partes adversas (litisconsórcio)
- [ ] Depende do tipo de processo

**[OBRIGATÓRIO] Q3.1.2:** Estrutura proposta:

```sql
CREATE TABLE partes_adversas (
    id SERIAL PRIMARY KEY,
    id_processo VARCHAR(50) REFERENCES processos(id_processo),
    tipo_parte VARCHAR(20),  -- 'autor' | 'reu' | 'terceiro_interessado' | 'reclamante' | 'reclamada'
    nome_completo VARCHAR(255) NOT NULL,
    nacionalidade VARCHAR(50),
    profissao VARCHAR(100),
    estado_civil VARCHAR(20),
    cpf_cnpj VARCHAR(18),
    rg_ie VARCHAR(20),
    email VARCHAR(255),
    telefone VARCHAR(20),
    nome_mae VARCHAR(255),
    -- Endereço
    cep VARCHAR(9),
    estado VARCHAR(2),
    cidade VARCHAR(100),
    bairro VARCHAR(100),
    logradouro VARCHAR(255),
    numero VARCHAR(10),
    complemento VARCHAR(100),
    -- Metadados
    tenant_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Essa estrutura está adequada?**
- [X] Sim, aprovar
- [ ] Não, ajustar: _______________

**[OBRIGATÓRIO] Q3.1.3:** Diferenciação Cliente vs Parte Adversa:
```
Campo processos.tipo_parte (autor/reu/terceiro) define a posição do CLIENTE.
A parte adversa é a posição OPOSTA.

Exemplo 1: Cliente é AUTOR → Parte adversa é RÉU
Exemplo 2: Cliente é RÉU → Parte adversa é AUTOR
```
**Essa lógica está correta?**
- [X] Sim
- [ ] Não, explicar: _______________

**[RECOMENDADO] Q3.1.4:** Busca automática de CEP:
- [X] API ViaCEP
- [ ] API Correios
- [ ] Outra: _______________
- [ ] Não implementar

---

## 4️⃣ ITEM 4 - IMPORTAÇÃO CSV DE PROCESSOS

### 4.1 Template CSV

**[OBRIGATÓRIO] Q4.1.1:** Forneça o **template CSV completo** com TODOS os campos esperados:

```csv
# EXEMPLO (ajuste conforme necessário):
nome_caso,numero_cnj,status,area_atuacao,fase,objeto_acao,valor_causa,advogado_oab,tipo_parte,parte_adversa_nome,parte_adversa_cpf,comarca,local_tramite,data_distribuicao,segredo_justica
"Ação de Cobrança",1234567-89.2024.8.26.0100,ATIVO,Civil,Postulatória,"Cobrança de honorários",50000.00,OAB123,autor,"João da Silva Réu",123.456.789-00,"São Paulo","1ª Vara Cível",2024-01-15,false
```

**Cole aqui o template desejado (com todos os campos do Item 1):**
```csv
[**Conforme indicação KELETY, nem sempre o advogado que está deixando o processo para um outro advogado/escritório fornece todas as informações do processo. Assim, podemos considerar somente o número CNJ/processo (20 posições) como obrigatório no CSV e incluir os demais campos semelhantes àqueles que temos no nosso cadastro de processos, como opcionais.**]
```

**[OBRIGATÓRIO] Q4.1.2:** Comportamento ao importar:
- [ ] Criar apenas processo + parte adversa (2 tabelas)
- [X] Criar processo + parte adversa + movimentação inicial ("Processo importado")
- [ ] Outro: _______________

**[RECOMENDADO] Q4.1.3:** Validação do número CNJ:
- [X] Verificar se já existe no BD (rejeitar duplicata)
- [ ] Permitir duplicata mas avisar
- [ ] Atualizar processo existente se CNJ duplicado
- [ ] Outro: _______________

**[RECOMENDADO] Q4.1.4:** Campos obrigatórios no CSV:
```
Marque os campos que DEVEM estar preenchidos:
X numero_cnj
X nome_caso
X area_atuacao
X tipo_parte
X parte_adversa_nome
☐ outros: _______________
```

---

## 5️⃣ ITEM 5 - CADASTRO DE CLIENTES

### 5.1 Campos Adicionais

**Campos Atuais:**
- `id_cliente, tipo_pessoa, nome_completo, cpf_cnpj, rg_ie, nacionalidade, estado_civil, profissao, endereco_completo, telefone, email, responsavel_pj, observacoes, data_cadastro, tenant_id`

**[OBRIGATÓRIO] Q5.1.1:** Novos campos propostos no Item 5:
```
X CEP (busca automática de endereço)
X Cidade (separada de endereco_completo)
X Estado (UF)
X Nome da Mãe
☐ Outros: _______________
```

**Aprovar adição?**
- [X] Sim, adicionar todos
- [ ] Não, manter estrutura atual
- [ ] Apenas: _______________

---

### 5.2 Campo de Documentos RAG

**[OBRIGATÓRIO] Q5.2.1:** Onde os documentos do RAG devem ser armazenados/referenciados?

**Situação Atual:**
- Documentos ficam em `./cases/{case_id}/documents/`
- RAG por **processo** (case_store)

**Proposta no Item 5:**
- "Campo específico e isolado para todos os documentos que dão sustentação ao caso jurídico"

**Clarificação necessária:**
```
☐ OPÇÃO A: Manter RAG por PROCESSO (atual)
   - Documentos organizados por caso
   - Campo no BD apenas para listar paths dos arquivos

☐ OPÇÃO B: Migrar RAG para CLIENTE
   - Todos documentos do cliente em um único vector store
   - Processos compartilham mesma base de conhecimento
   - ⚠️ Mudança arquitetural significativa

X OPÇÃO C: Híbrido (cliente + processo)
   - KB do cliente: documentos gerais (RG, contratos, histórico)
   - KB do processo: documentos específicos (petições, sentenças)

☐ Outro: _______________
```

**[OBRIGATÓRIO] Q5.2.2:** Estrutura da tabela `cliente_documentos` (se OPÇÃO A ou C):

```sql
CREATE TABLE cliente_documentos (
    id SERIAL PRIMARY KEY,
    id_cliente VARCHAR(50) REFERENCES clientes(id_cliente),
    id_processo VARCHAR(50) REFERENCES processos(id_processo),  -- NULL se documento geral do cliente
    nome_arquivo VARCHAR(255) NOT NULL,
    path_arquivo TEXT NOT NULL,
    tipo_documento VARCHAR(50),  -- 'RG', 'CPF', 'Contrato', 'Sentença', etc.
    data_upload TIMESTAMP DEFAULT NOW(),
    usuario_upload INT REFERENCES usuarios(id),
    indexado_rag BOOLEAN DEFAULT FALSE,  -- Se foi processado pelo RAG
    tenant_id VARCHAR(50)
);
```

**Essa estrutura está adequada?**
- [X] Sim, aprovar
- [ ] Não, ajustar: _______________

---

### 5.3 Ficha de Movimentações do Cliente

**[OBRIGATÓRIO] Q5.3.1:** A "Ficha de movimentações do cliente" é:
```
☐ Diferente da ficha de movimentações do PROCESSO
   - Registra: contatos, reuniões, alterações cadastrais, novos processos
   - Tabela: movimentacoes_clientes

☐ A mesma ficha (unificar em movimentacoes_gerais)
   - FK para clientes OU processos (ambos nullable)

X Não implementar (só movimentações de processo)
```

**[RECOMENDADO] Q5.3.2:** Se diferente, estrutura da `movimentacoes_clientes`:
```sql
CREATE TABLE movimentacoes_clientes (
    id SERIAL PRIMARY KEY,
    id_cliente VARCHAR(50) REFERENCES clientes(id_cliente),
    data_movimentacao TIMESTAMP NOT NULL,
    tipo_movimentacao VARCHAR(100),  -- 'Contato', 'Reunião', 'Alteração Cadastral', 'Novo Processo'
    descricao TEXT,
    usuario_responsavel INT REFERENCES usuarios(id),
    tenant_id VARCHAR(50)
);
```

---

### 5.4 Sistema de Agendamento

**[OBRIGATÓRIO] Q5.4.1:** Escopo do "Agendamento do cliente":
```
☐ Sistema COMPLETO de agenda (calendário, notificações, recorrência)
   - Funcionalidades: criar evento, editar, deletar, visualizar calendário mensal
   - Notificações: email, SMS, push
   - Integração: Google Calendar, Outlook
   - ⚠️ Desenvolvimento estimado: 80-120 horas

☐ Sistema BÁSICO (apenas registrar compromissos futuros)
   - Tabela agendamentos, lista simples, sem notificações
   - ⚠️ Desenvolvimento estimado: 15-25 horas

X Não implementar agora (roadmap futuro)
```

**[RECOMENDADO] Q5.4.2:** Estrutura da tabela `agendamentos`:

```sql
CREATE TABLE agendamentos (
    id SERIAL PRIMARY KEY,
    id_cliente VARCHAR(50) REFERENCES clientes(id_cliente),
    id_processo VARCHAR(50) REFERENCES processos(id_processo),  -- Opcional
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_hora TIMESTAMP NOT NULL,
    duracao_minutos INT DEFAULT 60,
    tipo_evento VARCHAR(50),  -- 'Reunião', 'Audiência', 'Prazo', 'Ligação'
    local VARCHAR(255),
    advogado_responsavel VARCHAR(20) REFERENCES advogados(oab),
    status VARCHAR(20) DEFAULT 'agendado',  -- 'agendado', 'concluido', 'cancelado'
    tenant_id VARCHAR(50)
);
```

---

## 6️⃣ ITEM 6 - ATUALIZAÇÃO AUTOMÁTICA DE CAMPOS

### 6.1 Trigger de Atualização

**[OBRIGATÓRIO] Q6.1.1:** Como detectar novos documentos ingeridos?
```
☐ Webhook/trigger no endpoint de upload
   - Quando arquivo é enviado via UI, dispara job de atualização

☐ Scheduled task (Celery Beat / APScheduler)
   - A cada X minutos, verifica pasta ./documents por novos arquivos

☐ Manual (botão "Recalcular análises")
   - Escritório clica quando adiciona documentos

☐ Combinação: _______________
```

**[OBRIGATÓRIO] Q6.1.2:** Campos a atualizar:
```
Quando novos documentos são adicionados ao RAG, recalcular:

X Resumo do Caso (análise FIRAC facts)
X Análise Estratégica (riscos legais + próximos passos)
X Análise FIRAC completa (facts, issue, rules, application, conclusion)
☐ Petições (NÃO - petições são geradas sob demanda, não atualizadas automaticamente)
☐ Outros: _______________
```

---

### 6.2 Armazenamento das Análises

**Situação Atual:**
- Análises ficam em cache JSON: `./cases/{case_id}/analysis_cache/`
- Não persistidas no BD

**[OBRIGATÓRIO] Q6.2.1:** Migrar análises para banco de dados?
```
☐ SIM - Criar tabela analises_processos:
   - id_processo (FK)
   - tipo_analise ('resumo', 'estrategia', 'firac', 'riscos')
   - conteudo_json (JSONB)
   - data_geracao (TIMESTAMP)
   - versao (INT) - para histórico
   - Vantagens: histórico, busca SQL, backup automático

☐ NÃO - Manter em cache de arquivos
   - Mais simples, menos mudanças
   - Desvantagens: sem histórico, backup manual

X HÍBRIDO - Cache + BD (melhor dos dois mundos)
   - Cache para acesso rápido
   - BD para persistência e histórico
```

---

### 6.3 Processamento Assíncrono

**[OBRIGATÓRIO] Q6.3.1:** Regenerar FIRAC pode levar 2-5 minutos. Como processar?
```
☐ Síncrono (usuário espera na tela)
   - ⚠️ Ruim para UX, timeout do navegador

X Assíncrono com job queue (Celery + Redis)
   - Usuário recebe "Processando..." e notificação ao concluir
   - ✅ Recomendado

☐ Assíncrono com threading simples (Python threads)
   - Mais leve, mas menos robusto

☐ Outro: _______________
```

**[RECOMENDADO] Q6.3.2:** Se assíncrono, estrutura de notificação:
```
☐ WebSocket (atualização em tempo real na UI)
☐ Polling (frontend consulta status a cada X segundos)
☐ Email ao concluir
X Apenas log no sistema (usuário verifica manualmente)
```

---

## 7️⃣ ITEM 7 - AUTOMAÇÃO DIÁRIA COM ROBOT PJE
OBSERVAÇÃO IMPORTANTE: 
A automação diária (que chamei aqui de robot pje) visa atender à padronização de comunicação entre os tribunais e advogados. Veja abaixo uma breve explanação do que se trata:
A plataforma comunica.pje.jus.br é um canal central para a comunicação oficial entre tribunais, advogados e outros usuários cadastrados no Processo Judicial Eletrônico (PJe), cumprindo a Resolução nº 234/2016 do Conselho Nacional de Justiça (CNJ) para unificar comunicações processuais eletrônicas. Ela integra ferramentas como o Diário de Justiça Eletrônico Nacional (DJEN), Domicílio Judicial Eletrônico e Plataforma de Editais, substituindo gradualmente meios tradicionais de intimação e citação. Saiba mais sobre a plataforma em Comunicações Processuais. 

Este arquivo 'robot_pje_v2.py' é um exercício que fiz sobre como acessar estas comunicações oficiais, utilizando para isto o número do CNJ/processo. O resultado desta busca deve ser registrado na Ficha de Processo e comunicado ao advogado responsável pelo processo.

Por favor, faça suas recomendações sobre a melhor forma de ter acesso a estas comunicações.
### 7.1 Scheduler

**[OBRIGATÓRIO] Q7.1.1:** Como executar `robot_pje_v2.py` diariamente?
```
☐ Cron job (Linux) - ex: 0 8 * * * /path/to/venv/python robot_pje_v2.py
☐ Task Scheduler (Windows) - tarefa agendada 08:00 AM
X Celery Beat (Python) - integrado ao app (PODE SER UMA BOA ALTERNATIVA?)
☐ APScheduler (Python) - mais leve que Celery
☐ AWS CloudWatch Events / Azure Functions (cloud)
☐ Outro: _______________
```

**[OBRIGATÓRIO] Q7.1.2:** Horário preferencial de execução:
```
X 08:00 AM (antes do expediente)
☐ 02:00 AM (madrugada, menos carga no servidor)
☐ Múltiplas vezes ao dia: 08:00, 14:00, 18:00
☐ Outro: _______________
```

---

### 7.2 Escalabilidade
**VEJA OBSERVAÇÕES ACIMA.**
**Situação Atual:**
- `robot_pje_v2.py` busca 1 processo por vez (input manual do número)

**[OBRIGATÓRIO] Q7.2.1:** Como buscar comunicações de TODOS os processos?
```
☐ OPÇÃO A: Loop pelos processos com numero_cnj preenchido
   - SELECT numero_cnj FROM processos WHERE numero_cnj IS NOT NULL
   - Para cada processo, executar robot_pje_v2.py
   - ⚠️ Pode levar horas se muitos processos

☐ OPÇÃO B: Apenas processos "ativos" ou com flag especifica
   - WHERE status = 'ATIVO' AND monitorar_comunicacoes = TRUE
   - Escritório controla quais processos monitorar

☐ OPÇÃO C: Processamento paralelo (múltiplas instâncias do robot)
   - ThreadPoolExecutor ou Celery workers
   - Busca 10 processos simultaneamente

☐ Outro: _______________
```

**[RECOMENDADO] Q7.2.2:** Tratamento de erros:
```
☐ Se um processo falhar, continuar os demais
☐ Se 3 processos seguidos falharem, abortar e alertar admin
☐ Retry automático (até 3 tentativas)
☐ Outro: _______________
```

---

### 7.3 Armazenamento das Comunicações
**VEJA OBSERVAÇÕES ACIMA.**
**[OBRIGATÓRIO] Q7.3.1:** Onde salvar comunicações baixadas pelo robot?
```
☐ Tabela comunicacoes_processuais no BD:
   - id_processo (FK)
   - data_comunicacao (TIMESTAMP)
   - tipo_comunicacao (VARCHAR) - ex: "Despacho", "Intimação"
   - conteudo_texto (TEXT) - conteúdo extraído
   - path_arquivo_pdf (TEXT) - se baixou PDF
   - origem (VARCHAR) - 'robot_pje'
   
☐ Apenas arquivos na pasta:
   - ./cases/{case_id}/comunicacoes/{data}_{tipo}.pdf
   - Criar movimentação_processual referenciando arquivo
   
☐ Ambos (BD + arquivo)
   - ✅ Recomendado

☐ Outro: _______________
```

**[RECOMENDADO] Q7.3.2:** Integração com RAG:
```
☐ Sim, indexar automaticamente comunicações no vector store do processo
X Não, apenas armazenar (advogado decide se adiciona ao RAG)
☐ Perguntar ao usuário via notificação
```

**[RECOMENDADO] Q7.3.3:** Notificação ao escritório:
**VEJA OBSERVAÇÕES ACIMA.**
```
☐ Email diário com resumo: "X novas comunicações encontradas"
☐ Push notification em tempo real
☐ Apenas log no sistema
☐ Dashboard com contador de "não lidas"
```

---

## 8️⃣ ITEM 8 - KB GLOBAL COM CRUD

### 8.1 Interface de Gerenciamento

**Situação Atual:**
- KB Global existe (`kb_store/`) mas sem UI
- Documentos adicionados manualmente via código

**[OBRIGATÓRIO] Q8.1.1:** Funcionalidades da interface:
```
☐ Listar documentos da KB Global (com filtros)
☐ Upload de novos documentos (PDF, DOCX, TXT)
☐ Editar metadados (título, categoria, tags)
☐ Deletar documentos
☐ Busca semântica (query no vector store)
☐ Preview/download de documentos
X Todas acima
☐ Outras: _______________
```

**[OBRIGATÓRIO] Q8.1.2:** Permissões de acesso:
```
☐ Apenas Admin pode editar KB Global
☐ Advogados podem adicionar, Admin pode deletar
☐ Todos usuários podem CRUD (democrático)
X Sistema de roles customizado: _______________
```

---

### 8.2 Sistema de Classificação

**[OBRIGATÓRIO] Q8.2.1:** Como classificar documentos?
```
☐ OPÇÃO A: Tags/labels livres (usuário digita)
   - Ex: "Civil", "Trabalhista", "Doutrina", "Jurisprudência"
   - Flexível mas inconsistente

☐ OPÇÃO B: Categorias pré-definidas (dropdown)
   - Lista fixa: Civil, Trabalhista, Penal, Família, etc.
   - Consistente mas menos flexível

☐ OPÇÃO C: Hierarquia de pastas virtuais
   - Área > Subtema > Tipo
   - Ex: Civil > Contratos > Doutrina
   
X OPÇÃO D: Combinação (categorias + tags)
   - Categoria obrigatória + tags opcionais
   - ✅ Recomendado
   - **CONSIDERAR CAMPO QUE IDENTIFIQUE O NÚMERO DA PASTA NO GOOGLE DRIVE / DROPBOX /** 

☐ Outro: _______________
```

**[RECOMENDADO] Q8.2.2:** Categorias iniciais sugeridas:
```
Forneça lista de categorias/subcategorias desejadas:

Exemplo:
- Processos Civil
  - Contratos
  - Responsabilidade Civil
  - Família e Sucessões
- Processos Trabalhistas
  - CLT
  - Acidentes de Trabalho
- Doutrinas Vigentes
- Jurisprudência
  - STF
  - STJ
  - Tribunais Regionais
- Legislação

[PREENCHER SUA ESTRUTURA]
```

---

### 8.3 Metadados dos Documentos

**[RECOMENDADO] Q8.3.1:** Estrutura da tabela `kb_global_documentos`: ÓTIMO

```sql
CREATE TABLE kb_global_documentos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    path_arquivo TEXT NOT NULL,
    categoria VARCHAR(100),
    tags TEXT[],  -- Array PostgreSQL
    tipo_documento VARCHAR(50),  -- 'PDF', 'DOCX', 'TXT'
    tamanho_bytes BIGINT,
    data_upload TIMESTAMP DEFAULT NOW(),
    usuario_upload INT REFERENCES usuarios(id),
    indexado_rag BOOLEAN DEFAULT FALSE,
    chroma_ids TEXT[],  -- IDs dos chunks no Chroma
    descricao TEXT,
    tenant_id VARCHAR(50)  -- Se multi-tenant
);
```

---

## 9️⃣ ITEM 9 - MÚLTIPLOS TIPOS DE PETIÇÕES

```python
VIDE 'PETICOES AREA CIVIL E PETICOES TRABALHISTAS' São dois arquivos PDF contidos na 
presente pasta. Contém o nome da petição e modelos. Vamos usá-los como referência inicial prevendo converter as petições para o padrão DOCX.

### 9.1 Tipos de Petição

**[OBRIGATÓRIO] Q9.1.1:** Liste **todos** os tipos de petição prioritários:


**Área Civil:**
```
☐ Petição Inicial (já implementado)
☐ Contestação
☐ Réplica
☐ Recurso de Apelação
☐ Agravo de Instrumento
☐ Embargos de Declaração
☐ Impugnação à Contestação
☐ Manifestação sobre Documentos
☐ Outros: _______________
```

**Área Trabalhista:**
```
☐ Reclamação Trabalhista Inicial (similar à Petição Inicial)
☐ Defesa / Contestação
☐ Recurso Ordinário
☐ Recurso de Revista
☐ Outros: _______________
```

**[OBRIGATÓRIO] Q9.1.2:** Priorização (ordem de implementação):
```
1. _______________ (já feito)
2. _______________
3. _______________
4. _______________
5. _______________
...
```

---

### 9.2 Lógica de Disponibilização

**[OBRIGATÓRIO] Q9.2.1:** Como determinar qual petição disponibilizar?
```
☐ OPÇÃO A: Baseado no campo processos.fase
   - Se fase = "Postulatória" → Petição Inicial
   - Se fase = "Contestação" → Petição de Contestação
   - Se fase = "Recursal" → Recurso de Apelação
   - Requerer mapeamento: fase → tipo_peticao

☐ OPÇÃO B: Baseado em movimentações_processuais
   - Se última movimentação = "Contestação juntada" → Réplica disponível
   - Lógica mais complexa mas precisa

☐ OPÇÃO C: Escritório escolhe manualmente (dropdown)
   - Mais flexível, sem automação

X OPÇÃO D: Combinação de A + C
   - Sistema sugere baseado na fase, usuário pode alterar

☐ Outro: _______________
```

---

### 9.3 Dados de Entrada Específicos

**[RECOMENDADO] Q9.3.1:** Petições diferentes precisam de dados diferentes. Exemplo:

**Petição Inicial:**
- Dados do juízo, partes, fatos, pedidos (já implementado)

**Contestação:**
- Dados da petição adversa
- Fatos contestados (checkboxes?)
- Argumentos de defesa
- Documentos probatórios

**Recurso de Apelação:**
- Dados da sentença recorrida
- Fundamentos do recurso
- Pedido de reforma/anulação

**Pergunta:** Cada tipo de petição terá:
```
☐ Formulário específico (tela customizada no frontend)
☐ Formulário genérico com campos dinâmicos (JSON schema)
☐ Apenas texto livre (menos estruturado)
☐ Outro: _______________
```

---

### 9.4 Templates LangChain

**[OBRIGATÓRIO] Q9.4.1:** Cada tipo de petição terá:
```
☐ Template LangChain separado (arquivo .py ou config)
☐ Prompt template centralizado com variáveis condicionais
☐ Sistema de templates customizáveis pelo escritório
☐ Outro: _______________
```

**[RECOMENDADO] Q9.4.2:** Quem cria os templates das petições?
```
☐ Equipe de desenvolvimento (hard-coded)
☐ Escritório fornece modelos em DOCX (convertidos para prompts)
☐ Sistema de editor de templates (avançado)
☐ Combinação: _______________
```

---

## 🔟 ITEM 10 - MODELO SAAS MULTI-TENANT
**POR FAVOR AVALIE ESTE DESCRITIVO EM ==> C:\adv-IA-2910\Referências SaaS para alternativa Google Cloud.pdf** E FAÇA SUAS RECOMENDAÇÕES.

### 10.1 Isolamento de Dados

**Status Atual:**
- Coluna `tenant_id` já existe em algumas tabelas
- `cadastro_manager.py` implementa filtragem básica

**[OBRIGATÓRIO] Q10.1.1:** Verificação de isolamento completo:
```
Tabelas que DEVEM ter tenant_id:
☐ escritorio (?)
☐ advogados
☐ clientes
☐ processos
☐ partes_adversas
☐ movimentacoes_processuais
☐ movimentacoes_clientes
☐ agendamentos
☐ cliente_documentos
☐ kb_global_documentos (?)
☐ comunicacoes_processuais
☐ analises_processos
☐ usuarios
☐ chat_turns

Obs: KB Global pode ser compartilhada entre tenants (jurisprudência, leis) ==> **NÃO. A KB GLOBAL DEVERÁ SER ESPECÍFICA PARA UM TENANT.**
```

**[OBRIGATÓRIO] Q10.1.2:** Estratégia de isolamento:
```
☐ Coluna tenant_id + RLS (Row Level Security) do PostgreSQL
   - Mais seguro, forçado pelo BD

☐ Apenas tenant_id + validação no backend
   - Mais simples, depende de código correto

☐ Schemas separados (schema per tenant)
   - Isolamento máximo, complexo

☐ Bancos de dados separados (DB per tenant)
   - Isolamento total, muito complexo

☐ Escolha: _______________
```

---

### 10.2 Registro de Novos Tenants

**[OBRIGATÓRIO] Q10.2.1:** Como novos escritórios se cadastram?
```
☐ Self-service (página pública de registro)
   - Escritório preenche formulário
   - Validação de email
   - Criação automática de tenant_id
   - ⚠️ Requer sistema de onboarding

☐ Manual via Admin
   - Admin cria tenant via painel
   - Envia credenciais por email
   - Mais controle, menos escalável

☐ Outro: _______________
```

**[RECOMENDADO] Q10.2.2:** Estrutura da tabela `tenants`:

```sql
CREATE TABLE tenants (
    tenant_id VARCHAR(50) PRIMARY KEY,
    nome_escritorio VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18),
    plano VARCHAR(20),  -- 'basico', 'profissional', 'enterprise'
    data_criacao TIMESTAMP DEFAULT NOW(),
    data_expiracao DATE,  -- Se plano com limite de tempo
    status VARCHAR(20) DEFAULT 'ativo',  -- 'ativo', 'suspenso', 'cancelado'
    limite_usuarios INT DEFAULT 5,
    limite_processos INT DEFAULT 100,
    limite_storage_gb INT DEFAULT 10,
    email_admin VARCHAR(255),
    configuracoes JSONB  -- Customizações específicas
);
```

---

### 10.3 Planos e Cobrança

**[OBRIGATÓRIO] Q10.3.1:** Haverá sistema de cobrança/billing?
```
☐ SIM - Implementar gateway de pagamento
   - Gateway: ☐ Stripe ☐ PagSeguro ☐ Mercado Pago ☐ Outro: ___
   - Planos: Básico (R$ X/mês), Profissional (R$ Y/mês), Enterprise
   - Cobrança automática mensal/anual
   - ⚠️ Desenvolvimento estimado: 60-100 horas

☐ NÃO (cobrança manual/offline)
   - Admin controla status manualmente
   - Mais simples

X FUTURO (versão 2.0)
   - Implementar SaaS básico agora, billing depois
```

**[RECOMENDADO] Q10.3.2:** Limites por plano:

| Recurso | Básico | Profissional | Enterprise |
|---------|--------|--------------|------------|
| Usuários | ___ | ___ | Ilimitado |
| Processos | ___ | ___ | Ilimitado |
| Storage (GB) | ___ | ___ | ___ |
| KB Global | Compartilhada | Privada | Privada |
| Suporte | Email | Email+Chat | Dedicado |
| Preço (R$/mês) | ___ | ___ | ___ |

---

### 10.4 Dashboard Admin

**[RECOMENDADO] Q10.4.1:** Painel administrativo SaaS:
```
☐ Listar todos tenants
☐ Ver métricas (usuários ativos, processos criados, storage usado)
☐ Suspender/ativar tenants
☐ Ajustar limites manualmente
☐ Ver logs de atividade
☐ Gráficos de crescimento (MRR, churn)
X Todas acima
☐ Outras: _______________
```

---

## 📊 PRIORIZAÇÃO E CRONOGRAMA

### Priorização Geral

**[OBRIGATÓRIO] P1:** Ordem de implementação dos 10 itens:

```
FASE 1 (MVP - 3 meses):
1. Item ___ 
2. Item ___
3. Item ___

FASE 2 (Expansão - 3 meses):
4. Item ___
5. Item ___
6. Item ___

FASE 3 (SaaS Completo - 6 meses):
7. Item ___
8. Item ___
9. Item ___
10. Item ___
```

**[RECOMENDADO] P2:** Prazos específicos:
```
☐ Sem deadline específico (implementar conforme possível)
☐ Deadline hard: ___ / ___ / ___
X Lançamento beta para clientes: _28__ / _11__ / _25__
☐ Go-live produção: ___ / ___ / ___
```

---

## 👥 EQUIPE E RECURSOS

**[RECOMENDADO] R1:** Equipe disponível:
```
- Desenvolvedores backend: ___
- Desenvolvedores frontend: ___
- DBA / DevOps: ___
- Designer UI/UX: ___
- QA / Tester: ___
```

**[RECOMENDADO] R2:** Ambiente de produção:
```
☐ AWS (EC2, RDS, S3)
☐ Azure
☐ Google Cloud
☐ Servidor on-premise / dedicado
X Ainda não definido
```

**[RECOMENDADO] R3:** Estratégia de testes:
```
☐ Testes unitários (pytest)
☐ Testes de integração
☐ Testes end-to-end (Selenium)
☐ Ambiente de staging
☐ Beta com clientes selecionados
☐ Outro: _______________
```

---

## 📎 ANEXOS E REFERÊNCIAS

**[OPCIONAL] A1:** Anexe documentos complementares:
```
☐ Diagrama ER completo (arquivo .png, .pdf ou link)
☐ Mockups de telas (Figma, Adobe XD)
☐ Exemplos de petições reais (DOCX anonimizados)
☐ Template CSV completo
☐ Documentação de APIs externas (DataJud, PJe)
☐ Outros: _______________

[Adicione links ou paths dos arquivos aqui]
```

---

## ✅ VALIDAÇÃO FINAL

**Checklist de Completude:**

- [ ] Todas perguntas [OBRIGATÓRIO] respondidas
- [ ] Template CSV fornecido (Q4.1.1)
- [ ] Tipos de petição listados (Q9.1.1)
- [ ] Priorização definida (Seção Priorização)
- [ ] Estruturas de BD revisadas
- [ ] Decisões sobre RAG esclarecidas (Q5.2.1)
- [ ] Estratégia SaaS definida (Q10.3.1)

**Data de Preenchimento:** _10__ / _11__ / 25___  
**Responsável:** ______PAULO_________  
**Próximo Passo:** Revisão técnica com equipe de desenvolvimento

---

## 📧 CONTATO PARA DÚVIDAS

**Em caso de dúvidas ao preencher:**
- Agende reunião com equipe técnica
- **Envie draft parcial para validação intermediária**
- Perguntas podem ser respondidas incrementalmente

**IMPORTANTE:** Quanto mais detalhado o preenchimento, menor o risco de retrabalho e mais precisa a estimativa de esforço/prazo.

---

*Documento gerado em 09/11/2025 para o projeto "Advocacia e IA"*
