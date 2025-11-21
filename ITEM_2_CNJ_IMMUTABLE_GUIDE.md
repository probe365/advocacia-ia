# 🔒 Item 2 - Trigger CNJ Imutável
## Guia de Implementação e Teste

**Data:** 14/11/2025  
**Status:** ✅ IMPLEMENTADO  
**Objetivo:** Impedir alteração do numero_cnj após criação do processo

---

## 📋 O QUE FOI IMPLEMENTADO

### 1. Migration PostgreSQL (Trigger)
**Arquivo:** `alembic/versions/0007_add_trigger_cnj_immutable.py`

**Funcionamento:**
- ✅ Trigger `trigger_prevent_cnj_update` executado BEFORE UPDATE
- ✅ Função `prevent_cnj_update()` verifica se numero_cnj mudou
- ✅ Se mudou: lança exceção com ERRCODE 23514 (check_violation)
- ✅ Mensagem clara: "O número CNJ não pode ser alterado após a criação do processo"
- ✅ Hint: "Se o número CNJ está incorreto, delete e recrie o processo"

**Executar migration:**
```powershell
cd C:\adv-IA-2910
.\venv\Scripts\activate
flask db upgrade
# Deve mostrar: ✅ Trigger de imutabilidade do numero_cnj criado com sucesso
```

**Verificar no PostgreSQL:**
```sql
-- Ver função criada
\df prevent_cnj_update

-- Ver trigger
SELECT * FROM pg_trigger WHERE tgname = 'trigger_prevent_cnj_update';

-- Testar manualmente (deve FALHAR)
UPDATE processos SET numero_cnj = '9999999-99.9999.9.99.9999' WHERE id_processo = 'algum_id';
-- Erro esperado: "O número CNJ não pode ser alterado após a criação do processo"
```

---

### 2. Validação Backend
**Arquivo:** `cadastro_manager.py` (linhas 254-273)

**Funcionamento:**
- ✅ Método `save_processo()` verifica UPDATE antes de executar
- ✅ Busca numero_cnj atual do processo no banco
- ✅ Compara com numero_cnj novo enviado
- ✅ Se diferente: lança `ValueError` com mensagem amigável
- ✅ Bloqueia antes do trigger (camada dupla de proteção)

**Código adicionado:**
```python
# === VALIDAÇÃO Item 2: Impedir alteração do numero_cnj ===
if dados.get("numero_cnj"):
    # Buscar numero_cnj atual do processo
    check_query = "SELECT numero_cnj FROM processos WHERE id_processo=%s"
    resultado = self._execute_query(check_query, check_params, fetch=True)
    
    if resultado:
        numero_cnj_atual = resultado[0].get('numero_cnj')
        numero_cnj_novo = dados.get("numero_cnj")
        
        # Se numero_cnj está sendo alterado, bloquear
        if numero_cnj_atual and numero_cnj_novo and numero_cnj_atual != numero_cnj_novo:
            raise ValueError(
                f"O número CNJ não pode ser alterado após a criação do processo. "
                f"Valor atual: {numero_cnj_atual}. "
                f"Se o número está incorreto, delete o processo e recrie-o."
            )
```

**Vantagens da validação backend:**
- Mensagem mais amigável que trigger SQL
- Mostra valor atual vs tentativa de alteração
- Resposta JSON estruturada via API
- Log de tentativas de alteração

---

### 3. Interface HTML
**Arquivo:** `templates/processo_edit.html`

**Mudanças implementadas:**

#### a) Campo readonly + disabled:
```html
<input type="text" class="form-control bg-light" id="numero_cnj" name="numero_cnj" 
       value="{{ processo.numero_cnj or '' }}"
       readonly
       disabled
       title="O número CNJ não pode ser alterado após a criação do processo">
```

#### b) Ícone de cadeado com tooltip:
```html
<label for="numero_cnj" class="form-label">
  Número CNJ 
  <i class="bi bi-lock-fill text-warning" 
     data-bs-toggle="tooltip" 
     data-bs-placement="top" 
     title="Campo protegido - Não pode ser alterado após criação do processo"></i>
</label>
```

#### c) Texto explicativo:
```html
<div class="form-text">
  <i class="bi bi-info-circle"></i> Formato: 0000000-00.0000.0.00.0000 
  <span class="text-warning">(campo imutável)</span>
</div>
```

#### d) Alerta no topo do formulário:
```html
{% if processo.numero_cnj %}
<div class="alert alert-warning alert-dismissible fade show" role="alert">
  <i class="bi bi-shield-lock-fill"></i> <strong>Atenção:</strong> 
  O <strong>número CNJ</strong> não pode ser alterado após a criação do processo 
  por questões de integridade e conformidade. 
  Se houver erro no número, será necessário excluir e recriar o processo.
  <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>
{% endif %}
```

#### e) Inicialização de tooltips:
```javascript
// Inicializar tooltips do Bootstrap 5
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
```

---

## 🧪 TESTES A REALIZAR

### Teste 1: Criar processo COM numero_cnj
```
1. Acesse /processos/<id_cliente>/novo
2. Preencha formulário com numero_cnj: 1234567-89.2024.8.26.0100
3. Salve o processo
4. ✅ Sucesso esperado: Processo criado normalmente
```

### Teste 2: Editar processo SEM alterar numero_cnj
```
1. Acesse /processos/<id_processo>/editar
2. Observe: Campo numero_cnj está readonly/disabled com ícone de cadeado
3. Altere outros campos (nome_caso, status, etc.)
4. Salve o processo
5. ✅ Sucesso esperado: Processo atualizado normalmente
```

### Teste 3: Tentar alterar numero_cnj via interface (DEVE FALHAR)
```
1. Acesse /processos/<id_processo>/editar
2. Tente editar campo numero_cnj (não conseguirá pois está disabled)
3. Abra DevTools Console
4. Execute: document.getElementById('numero_cnj').removeAttribute('readonly')
5. Execute: document.getElementById('numero_cnj').removeAttribute('disabled')
6. Altere valor do campo para: 9999999-99.2024.9.99.9999
7. Salve o formulário
8. ❌ Falha esperada: Erro "O número CNJ não pode ser alterado..."
```

### Teste 4: Tentar alterar via API (DEVE FALHAR)
```powershell
# Buscar id_processo de algum processo existente
$id_processo = "seu_id_processo_aqui"

# Tentar UPDATE com numero_cnj diferente
curl -X PUT http://127.0.0.1:5001/processos/$id_processo/salvar `
  -H "Content-Type: application/json" `
  -d '{
    "nome_caso": "Processo Teste",
    "numero_cnj": "9999999-99.2024.9.99.9999",
    "status": "ATIVO"
  }'

# ❌ Resposta esperada:
# {
#   "status": "erro",
#   "mensagem": "O número CNJ não pode ser alterado após a criação do processo. Valor atual: 1234567-89.2024.8.26.0100. ..."
# }
```

### Teste 5: Tentar UPDATE direto no PostgreSQL (DEVE FALHAR)
```sql
-- Conectar ao banco
psql -U postgres -d advocacia_ia_dev

-- Tentar alterar numero_cnj
UPDATE processos 
SET numero_cnj = '9999999-99.2024.9.99.9999' 
WHERE id_processo = 'seu_id_processo_aqui';

-- ❌ Erro esperado:
-- ERROR: O número CNJ não pode ser alterado após a criação do processo. 
--        Valor atual: 1234567-89.2024.8.26.0100, tentativa de alteração: 9999999-99.2024.9.99.9999
-- HINT: Se o número CNJ está incorreto, delete e recrie o processo
```

### Teste 6: Permitir UPDATE de outros campos (DEVE FUNCIONAR)
```sql
-- Alterar outros campos (nome_caso, status, etc.)
UPDATE processos 
SET nome_caso = 'Nome Alterado', 
    status = 'PENDENTE' 
WHERE id_processo = 'seu_id_processo_aqui';

-- ✅ Sucesso esperado: Query executada sem erros
```

### Teste 7: Permitir INSERT com numero_cnj (DEVE FUNCIONAR)
```sql
-- Criar novo processo com numero_cnj
INSERT INTO processos 
  (id_processo, id_cliente, tenant_id, nome_caso, numero_cnj, status, created_at)
VALUES 
  (gen_random_uuid(), 'id_cliente_teste', 'tenant_teste', 'Novo Processo', '5555555-55.2024.5.55.5555', 'ATIVO', NOW());

-- ✅ Sucesso esperado: Processo criado normalmente
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Backend:
- [x] Migration 0007 criada
- [ ] Migration 0007 executada (`flask db upgrade`)
- [ ] Trigger `trigger_prevent_cnj_update` existe no PostgreSQL
- [ ] Função `prevent_cnj_update()` existe no PostgreSQL
- [ ] Validação em `cadastro_manager.py` implementada
- [ ] Teste manual UPDATE via psql (deve falhar)
- [ ] Teste manual INSERT via psql (deve funcionar)

### Frontend:
- [x] Campo numero_cnj com `readonly` + `disabled`
- [x] Ícone de cadeado com tooltip
- [x] Texto explicativo "(campo imutável)"
- [x] Alerta no topo do formulário
- [x] Tooltips do Bootstrap inicializados
- [ ] Tooltip aparece ao passar mouse no ícone
- [ ] Alerta é visível no formulário de edição
- [ ] Campo numero_cnj visualmente diferente (bg-light)

### API:
- [ ] Tentativa de UPDATE com numero_cnj diferente retorna erro 400
- [ ] Mensagem de erro clara e amigável
- [ ] Resposta JSON estruturada
- [ ] Log de tentativa registrado

### Integração:
- [ ] Criar processo via interface funciona
- [ ] Editar processo (sem alterar CNJ) via interface funciona
- [ ] Tentar alterar CNJ via DevTools é bloqueado
- [ ] Tentar alterar CNJ via API é bloqueado
- [ ] Tentar alterar CNJ via psql é bloqueado
- [ ] CSV Import não tenta alterar CNJ de processos existentes

---

## 📊 CASOS DE USO COBERTOS

### ✅ Casos Permitidos:
1. **INSERT com numero_cnj:** Criar processo novo com CNJ
2. **INSERT sem numero_cnj:** Criar processo sem CNJ (NULL)
3. **UPDATE sem alterar numero_cnj:** Modificar outros campos
4. **UPDATE NULL → NULL:** Manter CNJ como NULL
5. **UPDATE NULL → valor:** Preencher CNJ pela primeira vez (se houver)

### ❌ Casos Bloqueados:
1. **UPDATE valor → outro valor:** Alterar CNJ existente
2. **UPDATE valor → NULL:** Remover CNJ existente
3. **UPDATE via qualquer método:** Interface, API, SQL direto

---

## 🔧 TROUBLESHOOTING

### Problema: Migration falha ao executar
```
Erro: função "prevent_cnj_update" já existe

Solução:
1. Verificar se migration já foi executada: flask db current
2. Se sim, pular: já está implementado
3. Se não, dropar função manualmente:
   DROP FUNCTION IF EXISTS prevent_cnj_update() CASCADE;
   DROP TRIGGER IF EXISTS trigger_prevent_cnj_update ON processos;
4. Executar novamente: flask db upgrade
```

### Problema: Campo numero_cnj ainda editável na interface
```
Solução:
1. Verificar se arquivo processo_edit.html foi salvo
2. Limpar cache do navegador (Ctrl+Shift+Delete)
3. Fazer hard reload (Ctrl+F5)
4. Verificar se está na página correta (/processos/<id>/editar)
```

### Problema: Tooltip não aparece
```
Solução:
1. Verificar se Bootstrap 5 está carregado no base.html
2. Verificar console do navegador por erros JavaScript
3. Verificar se código de inicialização de tooltips está presente
4. Testar: new bootstrap.Tooltip(document.querySelector('[data-bs-toggle="tooltip"]'))
```

### Problema: API não bloqueia alteração
```
Solução:
1. Verificar se save_processo() em cadastro_manager.py foi atualizado
2. Verificar logs do Flask: should see ValueError
3. Testar com Postman/curl com corpo JSON correto
4. Verificar se endpoint está usando CadastroManager atualizado
```

---

## 📚 DOCUMENTAÇÃO ADICIONAL

### Referências PostgreSQL:
- [Triggers](https://www.postgresql.org/docs/current/sql-createtrigger.html)
- [PL/pgSQL](https://www.postgresql.org/docs/current/plpgsql.html)
- [RAISE Exception](https://www.postgresql.org/docs/current/plpgsql-errors-and-messages.html)

### Referências Bootstrap:
- [Tooltips](https://getbootstrap.com/docs/5.3/components/tooltips/)
- [Alerts](https://getbootstrap.com/docs/5.3/components/alerts/)
- [Form Controls](https://getbootstrap.com/docs/5.3/forms/form-control/)

---

## ✅ STATUS FINAL

**Item 2 - Trigger CNJ Imutável:** ✅ **IMPLEMENTADO**

**Próximos Passos:**
1. Executar migration: `flask db upgrade`
2. Testar todos os casos de teste acima
3. Validar interface com usuário real
4. Documentar comportamento no manual do usuário

**Tempo estimado de testes:** 30-45 minutos

---

*Documentação criada: 14/11/2025*  
*Autor: GitHub Copilot*  
*Status: ✅ PRONTO PARA TESTES*
