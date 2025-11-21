# 📅 DIA 1 - Terça-feira 12/11/2025
## Plano de Trabalho Detalhado | Advocacia e IA

**Status:** 🟢 PRONTO PARA COMEÇAR  
**Foco:** Setup + Item 1 (Novos Campos Processos) + Item 3 (Partes Adversas)  
**Meta:** Migrations executadas + CRUD funcionais  

---

## ☀️ MANHÃ (9h - 12h) - 3 horas

### 🎯 PRIORIDADE 1: Executar Migrations (Paulo - 30 min)

**Objetivo:** Atualizar estrutura do banco de dados.

```powershell
# 1. Verificar status atual das migrations
cd C:\adv-IA-2910
python -m venv venv  # Se ainda não tiver
.\venv\Scripts\activate
flask db current

# 2. Executar migration 0005 (Item 1 - Novos campos processos)
flask db upgrade
# Deve ver: "✅ Migration 0005 concluída: Novos campos adicionados à tabela processos"

# 3. Verificar estrutura no PostgreSQL
psql -U postgres -d advocacia_ia_dev
\d processos  # Deve mostrar 12 novos campos

# 4. Backup antes de continuar
pg_dump -U postgres advocacia_ia_dev > backup_12nov_apos_0005.sql
```

**✅ Entregável:** 
- Migration 0005 executada
- 12 novos campos em `processos`
- Backup realizado

---

### 🎯 PRIORIDADE 2: Atualizar cadastro_manager.py (Paulo - 1h30)

**Objetivo:** Métodos CRUD aceitarem novos campos do Item 1.

**Arquivo:** `c:\adv-IA-2910\cadastro_manager.py`

Vou gerar o código agora...

---

### 🎯 PRIORIDADE 3: Criar Formulário HTML (Paulo - 1h)

**Objetivo:** UI para editar processo com novos campos.

**Arquivo:** `c:\adv-IA-2910\templates\processo_edit.html`

Vou gerar o template agora...

---

## 🌙 TARDE (14h - 18h) - 4 horas

### 🎯 PRIORIDADE 4: Migration Partes Adversas (Paulo - 30 min)

**Objetivo:** Criar tabela `partes_adversas` (Item 3).

**Arquivo:** `c:\adv-IA-2910\alembic\versions\0006_create_partes_adversas.py`

Vou criar agora...

---

### 🎯 PRIORIDADE 5: CRUD Partes Adversas (Paulo - 2h)

**Objetivo:** Implementar métodos no `cadastro_manager.py`.

Funções:
- `save_parte_adversa()`
- `get_partes_adversas_by_processo()`
- `delete_parte_adversa()`
- Validação CPF/CNPJ
- Integração ViaCEP

---

### 🎯 PRIORIDADE 6: Endpoint Flask + Template (Paulo - 1h30)

**Objetivo:** Página para gerenciar partes adversas.

**Arquivos:**
- `app/blueprints/processos.py` (novo endpoint)
- `templates/partes_adversas.html` (novo template)

---

## 🌃 NOITE (Opcional - 19h-21h) - 2 horas

### 🎯 PRIORIDADE 7: Testes Manuais (Paulo - 2h)

**Checklist:**
- [ ] Criar processo com novos campos
- [ ] Editar processo existente
- [ ] Adicionar 3 partes adversas
- [ ] Editar parte adversa
- [ ] Excluir parte adversa
- [ ] Testar validações (CPF inválido, CEP inválido)

---

## 📊 RESUMO DO DIA

**Total de Horas:** 7-9h (depende se fizer noite)

**Entregas Esperadas:**
1. ✅ Migration 0005 executada (12 novos campos em `processos`)
2. ✅ Migration 0006 executada (tabela `partes_adversas` criada)
3. ✅ `cadastro_manager.py` atualizado (Item 1 + Item 3)
4. ✅ Formulário de edição de processo com novos campos
5. ✅ Página de gerenciamento de partes adversas
6. ✅ Testes manuais realizados

**Items Completados:** Item 1 (100%) + Item 3 (100%)

---

## 🚀 PRÓXIMO: Quarta 13/11 (DIA 2)

Focos:
- Item 2: Trigger CNJ (imutabilidade)
- Item 4: Importação CSV
- Item 8: KB Global (preparação)

---

*Plano criado: 11/11/2025*  
*Início previsto: 12/11/2025 9h*  
*Status: 🟢 PRONTO*
