# Validação Intermediária - Questionário Técnico
## Projeto "Advocacia e IA" - Reformatação

**Data da Validação:** 10/11/2025  
**Responsável pela Revisão:** GitHub Copilot (Assistente Técnico)  
**Documento Analisado:** QUESTIONARIO_TECNICO_REFORMATACAO.md (versão preenchida)  
**Status:** ✅ DRAFT PARCIAL APROVADO COM RECOMENDAÇÕES

---

## 📊 RESUMO EXECUTIVO

### Completude do Preenchimento
- ✅ **Perguntas [OBRIGATÓRIO]:** 38/47 respondidas (81%)
- ✅ **Perguntas [RECOMENDADO]:** 24/32 respondidas (75%)
- ⚠️ **Decisões Críticas:** 3 pontos precisam de clarificação
- 🎯 **Qualidade Geral:** ALTA - Respostas objetivas e bem fundamentadas

### Decisões Principais Identificadas
1. ✅ Arquitetura híbrida RAG (cliente + processo)
2. ✅ Multi-tenant com isolamento por tenant_id
3. ✅ Processamento assíncrono com Celery
4. ✅ Importação CSV flexível (campos opcionais)
5. ⚠️ Robot PJe precisa de integração API (não apenas scraping)

---

## ✅ PONTOS FORTES DO PREENCHIMENTO

### 1. Modelo de Dados Bem Definido

**Item 1 - Cadastro de Processos:**
- ✅ Novos campos claramente especificados
- ✅ Decisão por estrutura hierárquica (instancia + subfase) é correta
- ✅ Campos booleanos simples (em_execucao, segredo_justica)
- ✅ Validação CNJ para versão futura (pragmático)

**Recomendação aceita:**
```sql
-- Separar campos de fase (conforme Q1.2.2 - Opção B)
ALTER TABLE processos
    ADD COLUMN instancia VARCHAR(20),  -- '1ª Instância' | '2ª Instância' | 'Recursal'
    ADD COLUMN subfase VARCHAR(50);     -- 'Postulatória' | 'Saneadora' | 'Instrutória' | 'Decisória'
```

---

### 2. Relacionamentos Claros

**Item 3 - Parte Adversa:**
- ✅ Relacionamento 1:N (múltiplas partes adversas) - adequado para litisconsórcio
- ✅ Estrutura completa com endereço
- ✅ API ViaCEP para busca automática

**Item 5 - Documentos RAG:**
- ✅ Arquitetura híbrida (OPÇÃO C) é a **melhor escolha**:
  - KB do cliente: Documentos gerais (RG, contratos, histórico)
  - KB do processo: Documentos específicos (petições, sentenças)
  - Permite flexibilidade e isolamento adequado

---

### 3. Decisões Pragmáticas

**Simplicidade First:**
- ✅ Não implementar agendamento completo agora (roadmap futuro)
- ✅ Não implementar movimentações_clientes (só processos)
- ✅ SaaS billing para versão 2.0
- ✅ Validação matemática CNJ para versão 2.0

**Essas decisões reduzem escopo e aceleram MVP** 🎯

---

## ⚠️ PONTOS QUE PRECISAM DE ATENÇÃO

### 1. Robot PJe - Comunicações Processuais (ITEM 7)

**Observação do usuário:**
> "A automação diária (robot pje) visa atender à padronização de comunicação entre os tribunais e advogados via comunica.pje.jus.br"

**⚠️ PROBLEMA IDENTIFICADO:**

O arquivo `robot_pje_v2.py` atual usa **web scraping** (Selenium/RPA), o que é:
- ❌ **Frágil:** Quebra se o site mudar
- ❌ **Lento:** 1 processo por vez
- ❌ **Limitado:** Não escalável para múltiplos processos

**✅ RECOMENDAÇÃO CRÍTICA:**

A plataforma **comunica.pje.jus.br** disponibiliza:
1. **API REST oficial** (se credenciada)
2. **DJEN (Diário de Justiça Eletrônico Nacional)** - dados estruturados
3. **DataJud API** (CNJ) - integrações oficiais

**Ação Necessária:**
```
☐ Investigar API oficial do comunica.pje.jus.br
☐ Verificar credenciamento necessário (OAB, certificado digital)
☐ Se API não disponível, considerar:
   - Parsing do DJEN (publicação diária em XML/JSON)
   - Integração com DataJud (já usado no projeto)
   - Manter robot como fallback temporário ==> não há API para o comunica.pje.jus.br. A alternativa parece estar com o uso do Selenium e o celery / redis.

☐ Documentar limitações do robot atual ==> acesso a um processo de cada vez.

--> a nossa solução tem que possibilitar o acesso de diversos processos no comunica.pje.jus.br confrontando com os processo que temos cadastrados no nosso app.
```

**Próximo Passo:**
- Reunião com Dr. Kelety para esclarecer acesso à API oficial ==> Até one pudemos ir não há API oficial
- Contato com CNJ/tribunal para credenciamento

---

### 2. Campos Duplicados/Redundantes (ITEM 1)

**⚠️ Campos que parecem duplicados:**

| Campo Proposto | Campo Existente | Clarificação Necessária |
|----------------|-----------------|-------------------------|
| `objeto_acao` | `nome_caso` | **Usuário confirmou: SÃO IGUAIS** ✅ Não criar objeto_acao |
| `responsavel` | `advogado_oab` | **Usuário confirmou: SÃO IGUAIS** ✅ Não criar responsavel |
| `status_processual` | `status` | **Usuário marcou: "Mesmo que tipo_parte"** ⚠️ ERRO PROVÁVEL |

**❌ INCONSISTÊNCIA DETECTADA:**

Em Q1.2.1, você marcou:
> `status_processual` = "Mesmo que **tipo_parte**"

Mas `tipo_parte` = autor/reu/terceiro (posição da parte)  
E `status` = ATIVO/ARQUIVADO/CONCLUÍDO (estado do processo) ==> **CONSIDERE ESTE ENTENDIMENTO.
**
**🔍 Pergunta de Clarificação:**
```
Q1.2.1 - ESCLARECIMENTO:

O campo `status_processual` deve ser:

A) ☐ IGUAL ao campo `status` existente (ATIVO, ARQUIVADO, CONCLUÍDO)
   → Não criar novo campo

B) ☐ DIFERENTE - novos valores (Em andamento, Suspenso, Sentenciado, etc.)
   → Criar campo status_processual + manter status atual

C) ☐ SUBSTITUIR o campo `status` atual
   → Renomear status → status_processual com novos valores
```

**Recomendação Técnica:** OK - ACEITA
- Se **A**: Não criar `status_processual` (duplicata)
- Se **B**: Criar ambos, documentar diferença semântica
- Se **C**: Migration Alembic para renomear coluna

---

### 3. Importação CSV - Template Incompleto (ITEM 4)

**Q4.1.1 - Template CSV:**

Você respondeu:
> "Considerar somente o número CNJ/processo (20 posições) como obrigatório no CSV"

✅ **Decisão correta!** (Pragmática conforme Dr. Kelety)

**⚠️ MAS: Template concreto não foi fornecido**

**Sugestão de Template Mínimo:** ==> PODE USAR ESTA SUGESTÃO MÍNIMA.

```csv
# Template CSV - Importação de Processos
# Campos OBRIGATÓRIOS: numero_cnj, nome_caso, area_atuacao, tipo_parte, parte_adversa_nome
# Campos OPCIONAIS: todos os demais

numero_cnj,nome_caso,area_atuacao,tipo_parte,parte_adversa_nome,parte_adversa_cpf,advogado_oab,comarca,local_tramite,data_distribuicao,valor_causa,fase,segredo_justica,observacoes
1234567-89.2024.8.26.0100,"Ação de Cobrança",Civil,autor,"João da Silva Réu",123.456.789-00,OAB123,"São Paulo","1ª Vara Cível",2024-01-15,50000.00,Postulatória,false,"Processo antigo migrado"
2345678-90.2023.5.15.0200,"Reclamação Trabalhista",Trabalhista,reclamante,"Empresa XYZ Ltda",12.345.678/0001-90,OAB456,"Campinas","2ª Vara do Trabalho",2023-06-10,25000.00,Instrutória,false,""
```

**Campos CSV recomendados:**
- ✅ Obrigatórios: `numero_cnj`, `nome_caso`, `area_atuacao`, `tipo_parte`, `parte_adversa_nome`
- ℹ️ Opcionais: Todos os 25+ campos do Item 1
- 🔧 Validação: Rejeitar linha se obrigatórios ausentes

**Ação Necessária:**
```
X Validar template CSV acima
☐ Adicionar/remover campos conforme necessidade
☐ Testar com dados reais do Dr. Kelety
```

---

### 4. Multi-Tenant - Isolamento KB Global (ITEM 10)

**Q10.1.1 - KB Global:**

Original do questionário:
> "KB Global pode ser compartilhada entre tenants (jurisprudência, leis)"

**Sua resposta:**
> "NÃO. A KB GLOBAL DEVERÁ SER ESPECÍFICA PARA UM TENANT."

✅ **Decisão entendida!** Mas implica em:

**Consequências Arquiteturais:**

1. **Duplicação de Dados:**
   - Cada tenant terá cópia de leis, jurisprudências comuns
   - Maior consumo de storage
   - Aumenta custo de armazenamento

2. **Vantagens:**
   - Isolamento total (segurança máxima)
   - Customização por escritório (cada um pode adicionar suas doutrinas)
   - Sem risco de "contaminação" de dados

3. **Alternativa Híbrida (Considerar):**
   ```
   - KB Pública (compartilhada): Leis federais, súmulas STF/STJ
     - tenant_id = NULL
     - Apenas leitura para todos
     - Admin central mantém
   
   - KB Privada (por tenant): Doutrinas, modelos, anotações
     - tenant_id = "escritorio_123"
     - CRUD completo pelo tenant
   ```

**🔍 Pergunta de Reavaliação:**
```
Você prefere:

A) ☐ KB Global 100% privada por tenant (sua resposta atual)
   - Cada escritório tem cópia de tudo
   - Mais storage, mais controle

B) ☐ Híbrida (compartilhada + privada)
   - Base comum de leis (compartilhada)
   - Documentos próprios (privados)
   - Menos storage, mais eficiência

C) X Avaliar futuramente
   - MVP: KB privada por tenant
   - V2.0: Adicionar KB compartilhada opcional
```

**Recomendação:** Opção **C** (pragmática - começar privado, evoluir) ==> OK

---

### 5. Petições - PDFs Fornecidos (ITEM 9)

**Observação do usuário:**
> "VIDE 'PETICOES AREA CIVIL E PETICOES TRABALHISTAS' - São dois arquivos PDF contidos na presente pasta"

**⚠️ ARQUIVOS NÃO ENCONTRADOS NA ANÁLISE**

**Ação Necessária:**
```
☐ Confirmar paths dos PDFs:
   - c:\adv-IA-2910\PETICOES AREA CIVIL.pdf ==> **C:\adv-IA-2910\Peticoes Área Civil.pdf**
   - c:\adv-IA-2910\PETICOES TRABALHISTAS.pdf ==> **C:\adv-IA-2910\Peticoes Trabalhistas.pdf**

☐ Após confirmação, analisar:
   - Quantos tipos de petição em cada área
   - Estrutura dos modelos (seções, campos variáveis)
   - Viabilidade de conversão DOCX → Prompt LangChain

X Priorizar 3-5 tipos mais usados para MVP
```

**Próximo Passo:**
- Enviar PDFs ou confirmar localização
- Revisão técnica dos modelos de petição

---

### 6. Prazo Beta - 28/11/2025 (ITEM Priorização)

**Sua resposta:**
> "Lançamento beta para clientes: 28/11/25"

**⚠️ ALERTA DE CRONOGRAMA:**

**Data atual:** 10/11/2025  
**Prazo beta:** 28/11/2025  
**Tempo disponível:** **18 dias úteis** ⏰

**Escopo proposto:**
- ✅ 10 itens de reformatação
- ✅ 15 novas tabelas no BD
- ✅ Migrations Alembic
- ✅ CRUD completo para novas entidades
- ✅ Integração Robot PJe
- ✅ Múltiplos tipos de petição
- ✅ Sistema multi-tenant

**⚠️ AVALIAÇÃO DE VIABILIDADE:**

| Item | Estimativa (horas) | Viável em 18 dias? |
|------|-------------------|-------------------|
| 1. Cadastro Processos (novos campos) | 12-16h | ✅ SIM |
| 2. Imutabilidade CNJ (trigger) | 2-4h | ✅ SIM |
| 3. Parte Adversa (CRUD) | 16-24h | ✅ SIM |
| 4. Importação CSV | 8-12h | ✅ SIM |
| 5. Cliente + RAG híbrido | 24-32h | ⚠️ JUSTO | ==> PODEMOS ESTENDER O PRAZO
| 6. Atualização automática (Celery) | 16-24h | ⚠️ JUSTO | ==> PODEMOS ESTENDER O PRAZO
| 7. Robot PJe automação | 20-30h | ❌ ARRISCADO |
| 8. KB Global CRUD | 12-20h | ✅ SIM |
| 9. Múltiplos tipos petição | 40-60h | ❌ NÃO | ==> **PODEMOS ESTENDER O PRAZO**
| 10. Multi-tenant completo | 16-24h | ⚠️ JUSTO | ==> PODEMOS COLOCAR ESTA TAREFA PARA O FINAL.
| **TOTAL** | **166-246h** | **❌ Inviável** |

**Horas disponíveis em 18 dias:**
- 1 dev full-time: ~144h (8h/dia)
- 2 devs full-time: ~288h

**🎯 RECOMENDAÇÃO - MVP para Beta 28/11:**

```
FASE 1 - MVP Beta (18 dias úteis):
✅ Item 1 - Novos campos processos (exceto fase complexa)
✅ Item 2 - Imutabilidade CNJ
✅ Item 3 - Parte Adversa CRUD
✅ Item 4 - Importação CSV básica
✅ Item 8 - KB Global (CRUD simples)
⚠️ Item 10 - Multi-tenant (isolamento básico, sem billing)

ADIADO PARA V2.0 (pós-beta):
📅 Item 5 - RAG híbrido (manter atual por processo)
📅 Item 6 - Atualização automática (manual por enquanto)
📅 Item 7 - Robot PJe (executar manualmente)
📅 Item 9 - Múltiplas petições (só Petição Inicial)

Estimativa MVP: ~88-120h (viável em 18 dias com 1-2 devs)
```

**Alternativa:**
```
Se prazo 28/11 é HARD DEADLINE: ==> É IMPORTANTE, PARA QUE SEJA APRESENTADO A POTENCIAIS CLIENTES NOS PRIMEIROS 15 DIAS DE DEZEMBRO. SEGUNDA METADE DE DEZEMBRO É SEMPRE DIFICIL ENCONTRAR PESSOAS CHAVE PARA APRESENTAÇÕES DO PROJETO.
→ Priorizar apenas Items 1, 2, 3, 4
→ Demo funcional com importação CSV + novos campos
→ Itens restantes em versão incremental pós-beta
```

---

## 🎯 DECISÕES PENDENTES (REQUEREM RESPOSTA)

### Decisão 1: status_processual vs status
**Prioridade:** 🔴 ALTA

```
Esclarecer se `status_processual` é:
A) Duplicata de `status` (não criar)
B) Campo novo com valores diferentes
C) Renomear `status` atual

Resposta: [X] ==> VER RESPOSTAS NO COMEÇO DESTA VALIDAÇÃO.
```

---

### Decisão 2: Robot PJe - API vs Scraping
**Prioridade:** 🔴 ALTA ==> PELAS INFORMAÇÕES QUE TEMOS (SEM API) Selenium + Celery + Redis

```
Investigar API oficial comunica.pje.jus.br:
- Contato com CNJ/Tribunal
- Credenciamento necessário
- Documentação API

Responsável: Dr. Kelety
Prazo: Antes de implementar Item 7
```

---

### Decisão 3: Prazo Beta - Escopo Realista
**Prioridade:** 🔴 CRÍTICA

```
Prazo 28/11/2025 (18 dias):
- Implementar TODOS os 10 itens (inviável)
- OU MVP reduzido (itens 1-4, 8, 10 básico)

Escolha: [ ]
```

---

### Decisão 4: Template CSV Concreto
**Prioridade:** 🟡 MÉDIA

```
Validar template CSV sugerido (vide seção 3)
Testar com dados reais do Dr. Kelety

Responsável: [ ]
Prazo: [ ]
```

---

### Decisão 5: KB Global - Compartilhada ou Privada
**Prioridade:** 🟢 BAIXA (pode decidir depois)

```
Manter 100% privada ou considerar híbrida?
Ver seção 4 acima.

Decisão: Avaliar em V2.0 (OK manter privada no MVP)
```

---

## 📋 CHECKLIST DE AÇÕES IMEDIATAS

### Antes de Implementar

- [ ] **CRÍTICO:** Definir escopo realista para beta 28/11
- [ ] **CRÍTICO:** Esclarecer campo `status_processual` (duplicata?)
- [ ] **CRÍTICO:** Investigar API oficial comunica.pje.jus.br
- [ ] Validar template CSV com dados reais
- [ ] Confirmar localização PDFs de petições
- [ ] Definir equipe (quantos devs disponíveis?)
- [ ] Criar planning poker / estimativa detalhada por item

### Documentação

- [ ] Atualizar DIAGRAMA_ER_TEMPLATE.md com decisões finalizadas
- [ ] Criar roadmap visual (Fase 1, 2, 3)
- [ ] Documentar arquitetura RAG híbrida
- [ ] Especificar integração Robot PJe (API ou scraping)

### Infraestrutura

- [ ] Decidir ambiente produção (AWS/GCP/Azure/on-premise)
- [ ] Setup Celery + Redis (Item 6)
- [ ] Configurar ambiente de staging
- [ ] Planejar testes de carga (múltiplos tenants)

---

## ✅ APROVAÇÕES E PONTOS POSITIVOS

### Decisões Técnicas Excelentes

1. ✅ **RAG Híbrido (OPÇÃO C)** - Arquitetura flexível e escalável
2. ✅ **Processamento Assíncrono (Celery)** - Necessário para FIRAC
3. ✅ **Importação CSV Flexível** - Pragmático (campos opcionais)
4. ✅ **Multi-tenant básico primeiro** - Billing depois (V2.0)
5. ✅ **Não criar agendamento completo** - Reduz escopo MVP
6. ✅ **Relacionamento 1:N para partes adversas** - Suporta litisconsórcio
7. ✅ **API ViaCEP** - Boa UX para endereços
8. ✅ **Ambos (Backend + BD)** para imutabilidade CNJ - Defesa em profundidade

### Estruturas SQL Aprovadas

- ✅ `movimentacoes_processuais` (Q1.3.1)
- ✅ `partes_adversas` (Q3.1.2)
- ✅ `cliente_documentos` (Q5.2.2)
- ✅ `tenants` (Q10.2.2) - adequada para MVP

---

## 🚦 STATUS FINAL DA VALIDAÇÃO

### Aprovação Geral: ✅ **APROVADO COM RESSALVAS**

**O questionário está 80% completo e bem estruturado.**

**Para prosseguir com implementação, resolver:**
1. 🔴 Definir escopo realista para 28/11 (MVP reduzido?)
2. 🔴 Esclarecer `status_processual` (duplicata ou novo?)
3. 🔴 Investigar API oficial PJe (alternativa ao robot)

**Sem essas clarificações, existe risco de:**
- Retrabalho por interpretação errada
- Não cumprir prazo beta
- Implementar solução frágil (robot scraping sem API)

---

## 📅 PRÓXIMOS PASSOS RECOMENDADOS

### Imediato (Esta Semana)

1. **Reunião de Alinhamento** com Dr. Kelety e equipe técnica:
   - Revisar esta validação
   - Decidir escopo MVP 28/11
   - Esclarecer decisões pendentes (3 críticas acima)
   - Definir responsabilidades

2. **Contato com CNJ/Tribunal:**
   - Verificar API oficial comunica.pje.jus.br
   - Alternativas: DataJud, parsing DJEN
   - Credenciamento necessário

3. **Criar Planning Detalhado:**
   - Quebrar itens em tasks menores
   - Estimar horas por task
   - Alocar devs (quem faz o quê)
   - Criar kanban/sprint (Jira, Trello, GitHub Projects)

### Semana 2 (11-15/11)

4. **Implementar MVP Core:**
   - Migrations Alembic (novos campos + tabelas)
   - CRUD básico (processos, partes adversas)
   - Importação CSV (validação + testes)

5. **Setup Infraestrutura:**
   - Ambiente staging
   - Celery + Redis (se Item 6 no MVP)
   - CI/CD pipeline

### Semana 3 (18-22/11)

6. **Features Avançadas:**
   - KB Global CRUD
   - Multi-tenant isolamento
   - Robot PJe (manual ou API)

7. **Testes e Ajustes:**
   - Testes de integração
   - Validação com dados reais
   - Correção de bugs

### Semana 4 (25-28/11)

8. **Preparação Beta:**
   - Documentação de uso
   - Treinamento Dr. Kelety
   - Deploy staging → produção
   - Go-live 28/11 🚀

---

## 💬 FEEDBACK SOBRE O PREENCHIMENTO

### Pontos Fortes
- ✅ Respostas objetivas (checkboxes marcados)
- ✅ Comentários adicionais quando necessário
- ✅ Decisões pragmáticas (reduzir escopo)
- ✅ Compreensão clara do negócio jurídico

### Pontos a Melhorar
- ⚠️ Algumas perguntas [RECOMENDADO] não respondidas
- ⚠️ Template CSV não fornecido concretamente
- ⚠️ PDFs de petições não localizados
- ⚠️ Equipe/recursos não especificados (seção 👥)

### Sugestões
- 📝 Completar seção "Equipe e Recursos" (R1, R2, R3)
- 📝 Anexar PDFs ou confirmar paths
- 📝 Revisar decisões críticas marcadas acima

---

## 📧 CONTATO PARA ESCLARECIMENTOS

**Próxima Iteração:**
- Agende reunião para discutir esta validação
- Esclareça 3 decisões críticas
- Confirme escopo MVP para 28/11

**Estou disponível para:**
- Refinar qualquer seção
- Criar documentos adicionais
- Iniciar implementação após aprovação final

---

## ✍️ ASSINATURAS

**Validação Técnica:**  
GitHub Copilot (Assistente IA)  
Data: 10/11/2025

**Próxima Revisão:**  
Paulo + Dr. Kelety + Equipe Técnica  
Data Prevista: ___/___/2025

---

**Status:** 🟡 AGUARDANDO ESCLARECIMENTOS CRÍTICOS  
**Progresso:** 80% completo  
**Confiança para Implementar:** 70% (aumenta para 95% após resolver 3 decisões críticas)

---

*Documento gerado em 10/11/2025 para validação intermediária do projeto "Advocacia e IA"*
