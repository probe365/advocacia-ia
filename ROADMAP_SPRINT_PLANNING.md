# 🚀 Roadmap - Projeto "Advocacia e IA" - Reformatação
## Sprint Planning Completo | Beta 28/11/2025

**Data de Criação:** 11/11/2025  
**Prazo Beta:** 28/11/2025 (17 dias úteis)  
**Prazo Fase 2:** 15/12/2025 (34 dias totais)  
**Equipe:** 4 pessoas (Paulo + 3 devs)  
**Status:** 🟢 EM PLANEJAMENTO

---

## 📊 VISÃO GERAL DO PROJETO

### Objetivo
Reformatar aplicação "Advocacia e IA" com 10 melhorias principais, preparando para modelo SaaS multi-tenant.

### Escopo Dividido em 2 Fases

**FASE 1 - MVP Beta (28/11):**
- Items 1, 2, 3, 4, 8, 10
- Infraestrutura base
- Demo funcional para clientes

**FASE 2 - Complemento (15/12):**
- Items 5, 6, 7, 9
- Features avançadas
- Refinamentos

---

## 🎯 FASE 1 - MVP BETA (11/11 → 28/11)

### Estimativa Total: 88-124 horas
### Divisão: 4 pessoas = 22-31h por pessoa
### Ritmo: 5-7h por semana por pessoa

---

## 📅 CRONOGRAMA DETALHADO - FASE 1

### **SEMANA 1: Setup + Core (11-15/11)**

#### **Segunda-feira 11/11 - DIA 1** ⏰ 8h de trabalho
**Sprint Goal:** Infraestrutura + Planejamento

**🔧 DevOps/Paulo (4h):**
- [X] Setup DigitalOcean Droplet (Ubuntu 22.04, 4GB RAM)
- [X] Instalar PostgreSQL 15 ==> JÁ INSTALADO.
- [X] Instalar Redis 7
- [ ] Configurar firewall (portas 22, 80, 443, 5432, 6379)
- [X] Criar database `advocacia_ia_prod`
- [X] Configurar usuário PostgreSQL `app_user`

**💻 Dev Backend #1 (4h):**
- [ ] Revisar documentação (QUESTIONARIO + VALIDACAO + DIAGRAMA_ER)
- [ ] Preparar ambiente local (clonar repo, venv, requirements)
- [ ] Conectar no PostgreSQL do DigitalOcean
- [ ] Testar conexão com banco
- [ ] Criar branch `feature/item-1-novos-campos`

**💻 Dev Backend #2 (4h):**
- [ ] Revisar documentação
- [ ] Preparar ambiente local
- [ ] Estudar estrutura atual de `processos` e `clientes`
- [ ] Criar branch `feature/item-3-parte-adversa`

**💻 Dev Backend #3 (4h):**
- [ ] Revisar documentação
- [ ] Preparar ambiente local
- [ ] Estudar sistema de RAG atual (`kb_store/`)
- [ ] Criar branch `feature/item-8-kb-global`

**📝 Entregável Dia 1:**
- Servidor DigitalOcean configurado ✅
- PostgreSQL + Redis funcionando ✅
- Time com ambiente local pronto ✅

---

#### **Terça-feira 12/11 - DIA 2** ⏰ 8h de trabalho
**Sprint Goal:** Migrations + Estrutura BD

**💻 Dev Backend #1 (6h) - ITEM 1:**
- [ ] Criar migration Alembic `0005_add_processos_fields.py`
- [ ] Adicionar novos campos em `processos`:
  ```sql
  - local_tramite TEXT
  - comarca VARCHAR(100)
  - area_atuacao VARCHAR(50)
  - instancia VARCHAR(20)
  - subfase VARCHAR(50)
  - assunto VARCHAR(255)
  - valor_causa DECIMAL(15,2)
  - data_distribuicao DATE
  - data_encerramento DATE
  - sentenca TEXT
  - em_execucao BOOLEAN DEFAULT FALSE
  - segredo_justica BOOLEAN DEFAULT FALSE
  ```
- [ ] Criar índices de performance
- [ ] Testar migration localmente
- [ ] Commit + Push

**💻 Dev Backend #2 (6h) - ITEM 3:**
- [ ] Criar migration Alembic `0006_create_partes_adversas.py`
- [ ] Criar tabela `partes_adversas` completa
- [ ] Foreign key para `processos`
- [ ] Índices (id_processo, cpf_cnpj, nome_completo)
- [ ] Testar migration localmente
- [ ] Commit + Push

**🔧 DevOps/Paulo (2h):**
- [ ] Executar migrations no servidor produção
- [ ] Backup do BD antes de migrar
- [ ] Validar estrutura nova
- [ ] Documentar credenciais (vault seguro)

**💻 Dev Backend #3 (6h) - ITEM 8:**
- [ ] Criar migration Alembic `0007_create_kb_global_documentos.py`
- [ ] Criar tabela `kb_global_documentos`
- [ ] Campos: titulo, path_arquivo, categoria, tags, tenant_id
- [ ] Índices (categoria, tags USING GIN)
- [ ] Testar migration localmente
- [ ] Commit + Push

**📝 Entregável Dia 2:**
- 3 migrations criadas ✅
- Estrutura BD atualizada em produção ✅
- Schema SQL documentado ✅

---

#### **Quarta-feira 13/11 - DIA 3** ⏰ 8h de trabalho
**Sprint Goal:** CRUD Endpoints - Parte 1

**💻 Dev Backend #1 (7h) - ITEM 1:**
- [ ] Atualizar `cadastro_manager.py`:
  - [ ] Método `save_processo()` - aceitar novos campos
  - [ ] Método `get_processo_by_id()` - retornar novos campos
  - [ ] Validações (area_atuacao, valor_causa, etc)
- [ ] Criar endpoint Flask `/processos/ui/<id>/edit`:
  - [ ] Formulário HTML com novos campos
  - [ ] Dropdowns (area_atuacao, instancia, subfase)
  - [ ] Input number (valor_causa)
  - [ ] Checkboxes (em_execucao, segredo_justica)
- [ ] Testar CRUD completo
- [ ] Commit + Push

**💻 Dev Backend #2 (7h) - ITEM 3:**
- [ ] Criar `cadastro_manager.py` - métodos parte adversa:
  - [ ] `save_parte_adversa(dados, id_parte=None)`
  - [ ] `get_partes_adversas_by_processo(id_processo)`
  - [ ] `get_parte_adversa_by_id(id_parte)`
  - [ ] `delete_parte_adversa(id_parte)`
- [ ] Criar endpoint Flask `/processos/<id>/partes-adversas`:
  - [ ] Listar partes adversas do processo
  - [ ] Formulário adicionar nova parte adversa
  - [ ] Integração API ViaCEP (busca por CEP)
  - [ ] Validação CPF/CNPJ
- [ ] Testar CRUD completo
- [ ] Commit + Push

**💻 Dev Backend #3 (7h) - ITEM 8:**
- [ ] Criar `kb_global_manager.py`:
  - [ ] `save_documento_kb(dados, arquivo)`
  - [ ] `get_documentos_kb(tenant_id, categoria=None)`
  - [ ] `delete_documento_kb(id_doc)`
  - [ ] Upload de arquivo (PDF, DOCX, TXT)
  - [ ] Mover arquivo para `./kb_global/{tenant_id}/`
- [ ] Criar endpoint Flask `/kb-global`:
  - [ ] Listar documentos (tabela com filtros)
  - [ ] Upload de novo documento
  - [ ] Classificação (categoria + tags)
  - [ ] Download de documento
- [ ] Testar CRUD completo
- [ ] Commit + Push

**📝 Entregável Dia 3:**
- CRUD processos com novos campos ✅
- CRUD partes adversas completo ✅
- CRUD KB Global funcional ✅

---

#### **Quinta-feira 14/11 - DIA 4** ⏰ 8h de trabalho
**Sprint Goal:** Validações + Triggers + Testes

**💻 Dev Backend #1 (6h) - ITEM 2:**
- [ ] Criar trigger PostgreSQL `prevent_cnj_update`:
  ```sql
  CREATE OR REPLACE FUNCTION prevent_cnj_update()
  RETURNS TRIGGER AS $$
  BEGIN
      IF OLD.numero_cnj IS NOT NULL AND NEW.numero_cnj != OLD.numero_cnj THEN
          -- Log de auditoria
          INSERT INTO audit_log (tabela, acao, usuario, descricao)
          VALUES ('processos', 'tentativa_update_cnj', current_user, 
                  'Tentativa de alterar CNJ: ' || OLD.numero_cnj || ' → ' || NEW.numero_cnj);
          
          RAISE EXCEPTION 'Número CNJ não pode ser alterado após definição';
      END IF;
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;
  ```
- [ ] Criar migration `0008_add_cnj_immutability.py`
- [ ] Validação no backend Flask (dupla segurança)
- [ ] Criar tabela `audit_log` para registros
- [ ] Testar tentativa de alterar CNJ (deve falhar)
- [ ] Commit + Push

**💻 Dev Backend #2 (6h) - ITEM 4 Preparação:**
- [ ] Criar `csv_import_manager.py`:
  - [ ] `validate_csv_row(row, linha_num)` - validar campos obrigatórios
  - [ ] `parse_csv_file(csv_content)` - ler CSV
  - [ ] `import_processos_from_csv(id_cliente, csv_content)`
  - [ ] Validação de duplicata (numero_cnj)
  - [ ] Criar parte adversa automaticamente
  - [ ] Criar movimentação inicial ("Processo importado")
- [ ] Testar com CSV de exemplo
- [ ] Commit + Push

**💻 Dev Backend #3 (6h) - ITEM 8 Melhorias:**
- [ ] Adicionar busca semântica em KB Global:
  - [ ] Endpoint `/kb-global/search`
  - [ ] Query no Chroma vector store
  - [ ] Retornar documentos relevantes
- [ ] Sistema de tags (autocomplete)
- [ ] Preview de documentos (PDF → imagem)
- [ ] Testes de upload (múltiplos arquivos)
- [ ] Commit + Push

**🔧 DevOps/Paulo (4h):**
- [ ] Deploy das alterações em staging
- [ ] Executar migrations novas (0008)
- [ ] Testar triggers manualmente
- [ ] Validar integridade do BD

**📝 Entregável Dia 4:**
- Imutabilidade CNJ garantida (BD + backend) ✅
- Preparação importação CSV ✅
- KB Global com busca ✅

---

#### **Sexta-feira 15/11 - DIA 5** ⏰ 8h de trabalho
**Sprint Goal:** Importação CSV + Testes Integração

**💻 Dev Backend #2 (7h) - ITEM 4:**
- [ ] Criar endpoint Flask `/clientes/<id>/importar-csv`:
  - [ ] Upload de arquivo CSV
  - [ ] Validação em tempo real
  - [ ] Barra de progresso (WebSocket ou polling)
  - [ ] Relatório de importação:
    * Processos criados
    * Erros encontrados
    * Download log de erros
- [ ] Template CSV de exemplo para download
- [ ] Testar com 10, 50, 100 processos
- [ ] Commit + Push

**💻 Time Todo (8h) - Testes Integração:**
- [ ] **Teste 1:** Criar processo com novos campos
- [ ] **Teste 2:** Adicionar 3 partes adversas a um processo
- [ ] **Teste 3:** Tentar alterar numero_cnj (deve falhar)
- [ ] **Teste 4:** Importar CSV com 20 processos
- [ ] **Teste 5:** Upload 5 documentos na KB Global
- [ ] **Teste 6:** Buscar por categoria na KB
- [ ] Corrigir bugs encontrados
- [ ] Documentar issues no GitHub

**📝 Entregável Dia 5 (FIM SEMANA 1):**
- Importação CSV funcional ✅
- Items 1, 2, 3, 4, 8 testados ✅
- Bugs críticos corrigidos ✅

---

### **SEMANA 2: Multi-tenant + Refinamentos (18-22/11)**

#### **Segunda-feira 18/11 - DIA 6** ⏰ 8h de trabalho
**Sprint Goal:** Multi-tenant - Isolamento

**💻 Dev Backend #1 + Paulo (8h) - ITEM 10:**
- [ ] Criar migration `0009_add_tenant_id_missing_tables.py`:
  - [ ] Adicionar `tenant_id` em tabelas sem:
    * `advogados`
    * `kb_global_documentos`
    * `movimentacoes_processuais`
    * `comunicacoes_processuais` (futura)
    * `analises_processos` (futura)
- [ ] Criar tabela `tenants`:
  ```sql
  CREATE TABLE tenants (
      tenant_id VARCHAR(50) PRIMARY KEY,
      nome_escritorio VARCHAR(255) NOT NULL,
      cnpj VARCHAR(18) UNIQUE,
      plano VARCHAR(20) DEFAULT 'basico',
      status VARCHAR(20) DEFAULT 'ativo',
      limite_usuarios INT DEFAULT 5,
      limite_processos INT DEFAULT 100,
      limite_storage_gb INT DEFAULT 10,
      email_admin VARCHAR(255),
      data_criacao TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Popular `tenants` com 3 tenants de teste:
  * "escritorio_demo"
  * "escritorio_kelety"
  * "escritorio_teste"
- [ ] Testar migration
- [ ] Commit + Push

**💻 Dev Backend #2 (8h) - ITEM 10:**
- [ ] Atualizar `cadastro_manager.py`:
  - [ ] Forçar filtro `tenant_id` em TODAS queries
  - [ ] Métodos `get_*()` - adicionar WHERE tenant_id = ?
  - [ ] Métodos `save_*()` - adicionar tenant_id automático
  - [ ] Validar isolamento (não vazar dados entre tenants)
- [ ] Criar middleware Flask:
  ```python
  @app.before_request
  def set_tenant_context():
      # Extrair tenant_id de: subdomain, header, session
      g.tenant_id = extract_tenant_id()
  ```
- [ ] Testar isolamento (criar dados em 2 tenants, verificar separação)
- [ ] Commit + Push

**💻 Dev Backend #3 (8h) - ITEM 10:**
- [ ] Criar endpoint `/admin/tenants`:
  - [ ] Listar todos tenants (apenas admin)
  - [ ] Criar novo tenant (formulário)
  - [ ] Ativar/suspender tenant
  - [ ] Ver métricas (usuários, processos, storage)
- [ ] Sistema de roles:
  - [ ] `admin` (super usuário)
  - [ ] `tenant_admin` (admin do escritório)
  - [ ] `user` (usuário comum)
- [ ] Commit + Push

**📝 Entregável Dia 6:**
- Multi-tenant estrutura completa ✅
- Isolamento de dados garantido ✅
- Painel admin tenants criado ✅

---

#### **Terça-feira 19/11 - DIA 7** ⏰ 8h de trabalho
**Sprint Goal:** Multi-tenant - Registro + UX

**💻 Dev Backend #1 (7h) - ITEM 10:**
- [ ] Criar fluxo de registro de novo tenant:
  - [ ] Página pública `/registrar-escritorio`
  - [ ] Formulário: nome, CNPJ, email, senha inicial
  - [ ] Validação de CNPJ (API ReceitaWS)
  - [ ] Geração automática de `tenant_id`
  - [ ] Criação de usuário admin inicial
  - [ ] Email de boas-vindas (usando Flask-Mail)
- [ ] Testar registro completo (end-to-end)
- [ ] Commit + Push

**💻 Dev Backend #2 (7h) - ITEM 10:**
- [ ] Implementar sistema de subdomínio:
  - [ ] `escritorio1.advocacia-ia.com.br`
  - [ ] `escritorio2.advocacia-ia.com.br`
  - [ ] Extrair tenant_id do subdomain
  - [ ] Configurar DNS wildcard (*.advocacia-ia.com.br)
  - [ ] Testar em staging
- [ ] Fallback para `/login?tenant=escritorio1` (se sem subdomínio)
- [ ] Commit + Push

**💻 Dev Backend #3 (7h) - ITEM 10:**
- [ ] Criar dashboard por tenant:
  - [ ] Estatísticas: total processos, clientes, documentos
  - [ ] Gráfico: processos por área (Civil, Trabalhista)
  - [ ] Alertas: limite de storage, limite de processos
  - [ ] Últimas movimentações
- [ ] Widget "Upgrade Plano" (placeholder para V2.0)
- [ ] Commit + Push

**📝 Entregável Dia 7:**
- Registro de novos tenants funcional ✅
- Sistema de subdomínio ativo ✅
- Dashboard tenant personalizado ✅

---

#### **Quarta-feira 20/11 - DIA 8** ⏰ 8h de trabalho
**Sprint Goal:** Testes + Correções

**💻 Time Todo (8h) - Testes Multi-tenant:**
- [ ] **Teste 1:** Registrar 3 novos tenants
- [ ] **Teste 2:** Criar processo no tenant A, verificar que tenant B não vê
- [ ] **Teste 3:** Upload documento KB no tenant A, verificar isolamento
- [ ] **Teste 4:** Importar CSV no tenant B, verificar isolamento
- [ ] **Teste 5:** Acessar via subdomínio (tenant1.advocacia-ia.com.br)
- [ ] **Teste 6:** Dashboard mostra apenas dados do tenant correto
- [ ] **Teste 7:** Admin vê todos tenants, tenant_admin vê apenas seu
- [ ] Corrigir bugs encontrados
- [ ] Melhorar UX onde necessário
- [ ] Commit + Push

**📝 Entregável Dia 8:**
- Multi-tenant 100% funcional ✅
- Isolamento validado ✅
- Bugs corrigidos ✅

---

#### **Quinta-feira 21/11 - DIA 9** ⏰ 8h de trabalho
**Sprint Goal:** Refinamentos + UX

**💻 Dev Backend #1 (7h):**
- [ ] Melhorar formulários:
  - [ ] Máscaras de input (CPF, CNPJ, CEP, telefone)
  - [ ] Validação client-side (JavaScript)
  - [ ] Feedback visual (campos obrigatórios)
  - [ ] Tooltips explicativos
- [ ] Responsividade mobile (Bootstrap)
- [ ] Commit + Push

**💻 Dev Backend #2 (7h):**
- [ ] Sistema de notificações:
  - [ ] Tabela `notificacoes` (id, tenant_id, usuario_id, mensagem, lida, created_at)
  - [ ] Notificar quando:
    * CSV importado com sucesso
    * Novo documento na KB
    * Limite de storage próximo
  - [ ] Badge com contador no navbar
  - [ ] Marcar como lida
- [ ] Commit + Push

**💻 Dev Backend #3 (7h):**
- [ ] Logs e auditoria:
  - [ ] Tabela `audit_log` aprimorada
  - [ ] Registrar ações importantes:
    * Login/logout
    * Criação/edição de processo
    * Alteração de tenant
  - [ ] Endpoint `/admin/logs` (apenas admin)
  - [ ] Filtros por: data, usuário, ação
- [ ] Commit + Push

**📝 Entregável Dia 9:**
- UX melhorada ✅
- Sistema de notificações ✅
- Auditoria implementada ✅

---

#### **Sexta-feira 22/11 - DIA 10** ⏰ 8h de trabalho
**Sprint Goal:** Testes Finais + Deploy Staging

**💻 Time Todo (4h) - Testes Finais:**
- [ ] Executar todos testes de integração novamente
- [ ] Testar em diferentes navegadores (Chrome, Firefox, Safari)
- [ ] Testar em mobile (responsividade)
- [ ] Validar performance (queries lentas?)
- [ ] Checklist completo de funcionalidades
- [ ] Documentar bugs encontrados

**🔧 DevOps/Paulo (4h) - Deploy Staging:**
- [ ] Backup completo do BD produção
- [ ] Deploy de todas alterações (Items 1-4, 8, 10)
- [ ] Executar migrations em ordem (0005 → 0009)
- [ ] Configurar Nginx (subdomínios wildcard)
- [ ] Configurar SSL (Let's Encrypt)
- [ ] Testar URL pública (staging.advocacia-ia.com.br)
- [ ] Criar 3 tenants de demo para apresentação

**📝 Entregável Dia 10 (FIM SEMANA 2):**
- Staging 100% funcional ✅
- URL pública acessível ✅
- Pronto para testes beta ✅

---

### **SEMANA 3: Preparação Beta (25-28/11)**

#### **Segunda-feira 25/11 - DIA 11** ⏰ 8h de trabalho
**Sprint Goal:** Correções Críticas + Documentação

**💻 Time Todo (8h):**
- [ ] Revisar todos issues abertos
- [ ] Priorizar correções críticas
- [ ] Dividir tarefas entre time
- [ ] Corrigir bugs bloqueadores
- [ ] Melhorar mensagens de erro
- [ ] Validar segurança (SQL injection, XSS)
- [ ] Commit + Push

**Paulo (4h):**
- [ ] Criar documentação de uso:
  - [ ] Como registrar escritório
  - [ ] Como importar processos via CSV
  - [ ] Como adicionar parte adversa
  - [ ] Como usar KB Global
  - [ ] FAQ comum
- [ ] Preparar slides apresentação
- [ ] Gravar vídeo demo (3-5 minutos)

**📝 Entregável Dia 11:**
- Bugs críticos corrigidos ✅
- Documentação de uso criada ✅
- Material de apresentação pronto ✅

---

#### **Terça-feira 26/11 - DIA 12** ⏰ 8h de trabalho
**Sprint Goal:** Deploy Produção + Testes Finais

**🔧 DevOps/Paulo (6h):**
- [ ] Configurar domínio definitivo (ex: app.advocacia-ia.com.br)
- [ ] Configurar DNS (A records, wildcard)
- [ ] Deploy produção (ambiente limpo)
- [ ] Executar migrations
- [ ] Popular dados de exemplo
- [ ] Configurar backup automático (diário)
- [ ] Configurar monitoramento (Uptime Robot)

**💻 Time Todo (6h):**
- [ ] Testes smoke em produção:
  - [ ] Registrar tenant real
  - [ ] Importar CSV real (fornecido por Dr. Kelety)
  - [ ] Criar processos completos
  - [ ] Testar todos fluxos principais
- [ ] Ajustes finais de UX
- [ ] Commit + Push (hotfixes se necessário)

**📝 Entregável Dia 12:**
- Produção 100% estável ✅
- Testes smoke passando ✅
- Sistema pronto para demo ✅

---

#### **Quarta-feira 27/11 - DIA 13** ⏰ 4h de trabalho
**Sprint Goal:** Treinamento + Ajustes Finais

**Paulo + Time (4h):**
- [ ] Treinamento interno com time
- [ ] Simulação de apresentação
- [ ] Últimos ajustes de UI
- [ ] Verificar dados de exemplo
- [ ] Preparar roteiro de demo
- [ ] Backup final antes do go-live

**📝 Entregável Dia 13:**
- Time treinado ✅
- Demo ensaiada ✅
- Sistema 100% pronto ✅

---

#### **🚀 Quinta-feira 28/11 - DIA 14 - GO-LIVE BETA**
**Sprint Goal:** LANÇAMENTO OFICIAL

**Manhã (9h-12h):**
- [ ] Verificação final de todos sistemas
- [ ] Teste de carga (simular 10 usuários simultâneos)
- [ ] Monitoramento ativo (logs, performance)
- [ ] Equipe em standby

**Tarde (14h-18h):**
- [ ] 🎉 **APRESENTAÇÃO BETA**
- [ ] Demo ao vivo para clientes potenciais
- [ ] Coletar feedback
- [ ] Registrar novos tenants
- [ ] Suporte em tempo real

**Noite (após apresentação):**
- [ ] Reunião de retrospectiva
- [ ] Documentar feedback recebido
- [ ] Priorizar ajustes para Fase 2
- [ ] Comemorar! 🍾

**📝 Entregável Dia 14:**
- ✅ **BETA LANÇADA COM SUCESSO!** 🚀
- Clientes potenciais usando ✅
- Feedback coletado ✅

---

#### **Sexta-feira 29/11 - DIA 15** ⏰ 4h de trabalho
**Sprint Goal:** Ajustes Pós-Demo

**💻 Time Todo (4h):**
- [ ] Corrigir bugs reportados na demo
- [ ] Implementar feedback urgente
- [ ] Melhorar pontos de UX problemáticos
- [ ] Documentar issues para Fase 2
- [ ] Deploy de hotfixes
- [ ] Monitorar estabilidade

**📝 Entregável Dia 15 (FIM FASE 1):**
- Beta estável e funcionando ✅
- Clientes usando sem problemas críticos ✅
- Backlog Fase 2 priorizado ✅

---

## 🎯 FASE 2 - COMPLEMENTO (02/12 → 15/12)

### Estimativa Total: 100-146 horas
### Divisão: 4 pessoas = 25-37h por pessoa
### Ritmo: 7-10h por semana por pessoa

---

### **SEMANA 4: RAG + Celery (02-06/12)**

#### **Segunda-feira 02/12 - DIA 16**
**Sprint Goal:** Setup Celery + Redis

**💻 Dev Backend #2 (8h) - ITEM 6:**
- [ ] Instalar Celery + Redis:
  ```bash
  pip install celery[redis] flower
  ```
- [ ] Criar `celery_app.py`:
  ```python
  from celery import Celery
  app = Celery('advocacia_ia',
               broker='redis://localhost:6379/0',
               backend='redis://localhost:6379/1')
  ```
- [ ] Configurar Celery Beat (scheduler)
- [ ] Criar primeira task de teste
- [ ] Testar execução assíncrona
- [ ] Commit + Push

**📝 Entregável:** Celery funcional ✅

---

#### **Terça-feira 03/12 - DIA 17**
**Sprint Goal:** RAG Híbrido (Cliente + Processo)

**💻 Dev Backend #1 + Paulo (8h) - ITEM 5:**
- [ ] Criar `kb_cliente_store/` (separado de `kb_store/`)
- [ ] Atualizar `ingestion_module.py`:
  - [ ] Método `_add_text_to_cliente_store()` (novo)
  - [ ] Diferenciar documentos de cliente vs processo
- [ ] Atualizar `pipeline.py`:
  - [ ] Buscar em ambos stores (cliente + processo)
  - [ ] Merge de resultados (documentos gerais + específicos)
- [ ] Testar com caso real
- [ ] Commit + Push

**📝 Entregável:** RAG híbrido funcionando ✅

---

#### **Quarta-feira 04/12 - DIA 18**
**Sprint Goal:** Atualização Automática de Análises

**💻 Dev Backend #2 (8h) - ITEM 6:**
- [ ] Criar Celery task `regenerar_analises`:
  ```python
  @celery.task
  def regenerar_analises(id_processo):
      # Re-executar FIRAC
      # Re-executar análise estratégica
      # Salvar em analises_processos (BD)
  ```
- [ ] Criar trigger no upload de documento:
  ```python
  @app.route('/processos/<id>/upload', methods=['POST'])
  def upload_documento(id):
      # Salvar arquivo
      # Indexar no RAG
      # Disparar task assíncrona
      regenerar_analises.delay(id)
  ```
- [ ] Criar tabela `analises_processos` (BD)
- [ ] Testar fluxo completo
- [ ] Commit + Push

**📝 Entregável:** Atualização automática funcionando ✅

---

#### **Quinta-feira 05/12 - DIA 19**
**Sprint Goal:** Robot PJe com Celery

**💻 Dev Backend #3 (8h) - ITEM 7:**
- [ ] Refatorar `robot_pje_v2.py` para ser task Celery:
  ```python
  @celery.task
  def buscar_comunicacoes_pje(numero_cnj):
      # Selenium scraping
      # Salvar em comunicacoes_processuais
      # Criar movimentacao_processual
  ```
- [ ] Criar job diário (Celery Beat):
  ```python
  @celery.beat_schedule
  def automacao_diaria_pje():
      processos = get_processos_monitorados()
      for p in processos:
          buscar_comunicacoes_pje.delay(p.numero_cnj)
  ```
- [ ] Configurar 5 workers paralelos
- [ ] Testar com 10 processos
- [ ] Commit + Push

**📝 Entregável:** Robot PJe automatizado ✅

---

#### **Sexta-feira 06/12 - DIA 20**
**Sprint Goal:** Análise PDFs + Dockerização

**Paulo + Dev #1 (4h) - ITEM 9:**
- [ ] Ler PDFs (`Peticoes Área Civil.pdf`, `Peticoes Trabalhistas.pdf`)
- [ ] Identificar 2-3 tipos prioritários:
  * Petição Inicial (já feito)
  * Contestação (Civil)
  * Reclamação Trabalhista (Trabalhista)
- [ ] Extrair estrutura de cada modelo
- [ ] Mapear campos variáveis
- [ ] Criar issue detalhado para implementação
- [ ] Commit + Push (documentação)

**💻 Dev Backend #2 + #3 (4h) - ITEM 11 (NOVO): DOCKERIZAÇÃO**
- [ ] Criar `Dockerfile` otimizado:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["gunicorn", "wsgi:app"]
  ```
- [ ] Criar `docker-compose.yml`:
  ```yaml
  services:
    db:
      image: postgres:15-alpine
      environment:
        POSTGRES_DB: advocacia_ia_prod
        POSTGRES_USER: app_user
        POSTGRES_PASSWORD: ${DB_PASSWORD}
      volumes:
        - postgres_data:/var/lib/postgresql/data
    
    redis:
      image: redis:7-alpine
      command: redis-server --requirepass ${REDIS_PASSWORD}
    
    app:
      build: .
      depends_on:
        - db
        - redis
      environment:
        DATABASE_URL: postgresql://app_user:${DB_PASSWORD}@db:5432/advocacia_ia_prod
        REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      volumes:
        - ./uploads:/app/uploads
        - ./kb_store:/app/kb_store
    
    celery_worker:
      build: .
      command: celery -A celery_app worker --loglevel=info
      depends_on:
        - db
        - redis
      deploy:
        replicas: 5  # 5 workers paralelos
    
    celery_beat:
      build: .
      command: celery -A celery_app beat --loglevel=info
      depends_on:
        - db
        - redis
    
    nginx:
      image: nginx:alpine
      ports:
        - "80:80"
        - "443:443"
      volumes:
        - ./nginx.conf:/etc/nginx/nginx.conf
        - ./static:/app/static
        - ./certbot:/etc/letsencrypt
      depends_on:
        - app
  
  volumes:
    postgres_data:
  ```
- [ ] Criar `.dockerignore`:
  ```
  .venv/
  __pycache__/
  *.pyc
  .env
  .git/
  *.log
  ```
- [ ] Criar `nginx.conf` para proxy reverso
- [ ] Testar localmente: `docker-compose up`
- [ ] Documentar deployment com Docker
- [ ] Commit + Push

**📝 Entregável:** Escopo Item 9 definido ✅ + Docker pronto para produção ✅

---

### **SEMANA 5: Petições + Finalização (09-13/12)**

#### **Segunda-feira 09/12 - DIA 21**
**Sprint Goal:** Implementar Contestação (Civil)

**Paulo + Dev #1 (8h) - ITEM 9:**
- [ ] Criar `petition_module.py` - método `generate_contestacao()`:
  ```python
  def generate_contestacao(dados_ui, firac_data, dados_peticao_adversa):
      # Prompt LangChain específico
      # Seções: Preliminares, Mérito, Provas, Pedidos
      # Retornar texto da contestação
  ```
- [ ] Criar endpoint `/processos/<id>/peticao/contestacao`
- [ ] Formulário de entrada (dados específicos)
- [ ] Testar geração
- [ ] Commit + Push

**📝 Entregável:** Contestação funcionando ✅

---

#### **Terça-feira 10/12 - DIA 22**
**Sprint Goal:** Implementar Reclamação Trabalhista

**Paulo + Dev #1 (8h) - ITEM 9:**
- [ ] Criar `petition_module.py` - método `generate_reclamacao_trabalhista()`:
  ```python
  def generate_reclamacao_trabalhista(dados_ui, firac_data):
      # Prompt LangChain específico
      # Seções: Qualificação, Fatos, Pedidos
      # Retornar texto da reclamação
  ```
- [ ] Criar endpoint `/processos/<id>/peticao/reclamacao-trabalhista`
- [ ] Formulário de entrada
- [ ] Testar geração
- [ ] Commit + Push

**📝 Entregável:** Reclamação Trabalhista funcionando ✅

---

#### **Quarta-feira 11/12 - DIA 23**
**Sprint Goal:** Testes Integração Fase 2

**💻 Time Todo (8h):**
- [ ] **Teste 1:** Upload documento → análise atualiza automaticamente
- [ ] **Teste 2:** Robot PJe busca comunicações de 10 processos
- [ ] **Teste 3:** RAG híbrido (busca em cliente + processo)
- [ ] **Teste 4:** Gerar Contestação completa
- [ ] **Teste 5:** Gerar Reclamação Trabalhista completa
- [ ] **Teste 6:** Monitorar Celery (5 workers paralelos)
- [ ] Corrigir bugs
- [ ] Otimizar performance

**📝 Entregável:** Fase 2 testada ✅

---

#### **Quinta-feira 12/12 - DIA 24**
**Sprint Goal:** Deploy Fase 2

**🔧 DevOps/Paulo (4h):**
- [ ] Deploy Items 5, 6, 7, 9 em produção
- [ ] Configurar Celery como serviço (systemd)
- [ ] Configurar Celery Beat (cron job)
- [ ] Monitorar workers (Flower dashboard)
- [ ] Backup BD

**💻 Time Todo (4h):**
- [ ] Testes em produção
- [ ] Validar todas features
- [ ] Documentar novas funcionalidades
- [ ] Atualizar FAQ

**📝 Entregável:** Fase 2 em produção ✅

---

#### **Sexta-feira 13/12 - DIA 25**
**Sprint Goal:** Refinamentos Finais

**💻 Time Todo (8h):**
- [ ] Melhorar UX baseado em feedback beta
- [ ] Otimizar queries lentas
- [ ] Adicionar índices faltantes
- [ ] Melhorar mensagens de erro
- [ ] Polir interface
- [ ] Documentação final
- [ ] Preparar para apresentação 15/12

**📝 Entregável:** Sistema completo e polido ✅

---

## 🎯 **Segunda-feira 15/12 - APRESENTAÇÃO FINAL** 🚀

**Manhã:**
- [ ] Verificação final
- [ ] Demo completa para clientes
- [ ] Mostrar todas features (Fase 1 + Fase 2)

**Tarde:**
- [ ] Coletar feedback
- [ ] Reunião de retrospectiva
- [ ] Planejar próximos passos (V2.0)
- [ ] 🎉 **COMEMORAÇÃO!**

---

## 📊 MÉTRICAS DE SUCESSO

### KPIs Fase 1 (28/11):
- [ ] 6 itens implementados (1, 2, 3, 4, 8, 10)
- [ ] Sistema multi-tenant funcional
- [ ] 3+ tenants registrados
- [ ] 0 bugs críticos
- [ ] Demo bem-sucedida

### KPIs Fase 2 (15/12):
- [ ] 10 itens implementados (todos)
- [ ] 3 tipos de petições funcionando
- [ ] Robot PJe automatizado
- [ ] Celery com 5 workers
- [ ] 10+ tenants ativos

---

## 🚨 GESTÃO DE RISCOS

### Riscos Identificados:

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Atraso em migrations | Média | Alto | Testar localmente antes de prod |
| Bugs em multi-tenant | Alta | Crítico | Testes extensivos de isolamento |
| Robot PJe quebrar (site mudar) | Média | Médio | Monitorar logs, ter fallback manual |
| Celery não escalar | Baixa | Médio | Configurar 5 workers, monitorar |
| Prazo apertado | Alta | Alto | Priorizar MVP, adiar features secundárias |

---

## 📞 COMUNICAÇÃO DO TIME

### Daily Standup (15 minutos diários - 9h):
- O que fiz ontem?
- O que farei hoje?
- Algum bloqueio?

### Reuniões Semanais (Sextas 16h):
- Retrospectiva da semana
- Planejar próxima semana
- Celebrar conquistas

### Ferramentas:
- **GitHub Projects:** Kanban board
- **Slack/Discord:** Comunicação assíncrona
- **GitHub Issues:** Bugs e features
- **Google Drive:** Documentação compartilhada

---

## ✅ CHECKLIST DE PROGRESSO

### Semana 1 (11-15/11):
- [ ] Infraestrutura DigitalOcean
- [ ] Items 1, 2, 3, 4, 8 implementados
- [ ] Testes integração passando

### Semana 2 (18-22/11):
- [ ] Item 10 (multi-tenant) completo
- [ ] Deploy staging
- [ ] Testes finais

### Semana 3 (25-28/11):
- [ ] Correções críticas
- [ ] Deploy produção
- [ ] 🚀 **GO-LIVE BETA 28/11**

### Semana 4 (02-06/12):
- [ ] Items 5, 6, 7 implementados
- [ ] Celery + Robot PJe funcionando

### Semana 5 (09-13/12):
- [ ] Item 9 (petições) completo
- [ ] Testes Fase 2
- [ ] Deploy final

### 15/12:
- [ ] 🎉 **APRESENTAÇÃO FINAL**

---

## 🎯 PRÓXIMA AÇÃO IMEDIATA

**Amanhã (12/11) - Segunda-feira:**
1. Setup DigitalOcean (Paulo/DevOps)
2. Criar migrations Items 1, 3, 8 (Devs #1, #2, #3)
3. Preparar ambiente local (Time todo)

**Esta semana:** Completar Semana 1 do roadmap

---

*Documento criado em 11/11/2025*  
*Última atualização: 11/11/2025*  
*Status: 🟢 PRONTO PARA EXECUÇÃO*
