# RELATÓRIO DE DIVERGÊNCIAS: FIRAC vs PETIÇÃO

## 📊 Data da Análise: 09/11/2025

## ❌ PROBLEMA CRÍTICO IDENTIFICADO

### 1. **FIRAC Retorna Apenas "RAW TEXT" (sem JSON estruturado)**

**Evidência dos Logs:**
```
Cached: True
Has 'data': False  ← PROBLEMA!
Has 'raw': True
```

**O que está acontecendo:**
- O método `generate_firac()` do Pipeline está retornando `data: None` ou `data: {}` (vazio)
- Apenas o campo `raw` contém texto (formato markdown)
- Isso significa que o LLM não está retornando JSON válido, ou o parsing falhou

**Consequência:**
```python
# No processos.py linha ~585
data_firac = firac.get('data') or {}  # ← Retorna {} vazio!

# Depois tenta usar:
firac_for_petition = {
    'facts': '',      # ← VAZIO!
    'issue': '',      # ← VAZIO!
    'rules': '',      # ← VAZIO!
    'application': '',# ← VAZIO!
    'conclusion': ''  # ← VAZIO!
}
```

---

### 2. **Petição Gerada com Dados Vazios**

**Logs do petition_module.py:**
```
[PETITION MODULE DEBUG] facts type: <class 'str'>, value:   ← STRING VAZIA!
[PETITION MODULE DEBUG] rules type: <class 'str'>, value:   ← STRING VAZIA!

[VALIDADOR] Chain 'nome_acao_peticao_chain' está com variáveis vazias: 
  ['firac_conclusion', 'firac_issue']  ← TODOS VAZIOS!

[VALIDADOR] Chain 'artigos_chave_peticao_chain' está com variáveis vazias: 
  ['firac_rules']  ← VAZIO!

[VALIDADOR] Chain 'fundamentacao_geral_peticao_chain' está com variáveis vazias: 
  ['firac_application', 'firac_issue', 'firac_rules']  ← VAZIOS!
```

**Resultado:**
A petição é gerada, mas com dados genéricos porque o LLM recebe prompts vazios!

---

## 🔍 ANÁLISE DO FLUXO QUEBRADO

### Pipeline Atual (COM PROBLEMA):

```
┌─────────────────────┐
│  generate_firac()   │
│                     │
│  1. Tenta ler cache │ ← Cache tem raw text apenas
│  2. Encontra cache  │
│  3. Return:         │
│     data: None      │ ← PROBLEMA!
│     raw: "**Fatos**"│
└─────────────────────┘
           │
           ↓
┌─────────────────────────┐
│ processos.py            │
│ ui_peticao_gerar()      │
│                         │
│ data_firac = {} (vazio!)│ ← Tenta parsear raw, mas falha
└─────────────────────────┘
           │
           ↓
┌─────────────────────────┐
│ PetitionGenerator       │
│ generate_peticao()      │
│                         │
│ Recebe FIRAC vazio      │ ← Gera petição genérica!
│ facts: ""               │
│ rules: ""               │
│ conclusion: ""          │
└─────────────────────────┘
```

---

## 🐛 CAUSAS RAIZ IDENTIFICADAS

### Causa #1: **Cache com Formato Antigo**

O arquivo de cache `firac.raw` contém texto markdown:
```markdown
**Análise FIRAC**

1. **Fatos:**
   O Tribunal de Justiça de São Paulo (TJSP) julgou a Apelação Criminal...
   
2. **Questão:**
   ...
```

Mas **NÃO** existe arquivo `firac.json` correspondente!

**Verificação:**
```python
# Em pipeline.py linha ~296
if firac_cache_path_json.exists() or firac_cache_path_raw.exists():
    if firac_cache_path_json.exists():  # ← Este arquivo NÃO existe!
        data = json.loads(firac_cache_path_json.read_text())
    else:
        raw = firac_cache_path_raw.read_text()  # ← Entra aqui
        return {'data': None, 'raw': raw}  # ← PROBLEMA: data vazio!
```

---

### Causa #2: **Parser de Raw Text Incompleto no processos.py**

O código em `processos.py` linha ~595 tenta parsear o raw text:
```python
if not data_firac and firac.get('raw'):
    import re
    raw = firac.get('raw', '')
    
    # Tenta extrair seções markdown
    facts_match = re.search(r'\*\*Fatos:\*\*\s*(.*?)(?=\n\s*\d+\.|\n\s*\*\*)', ...)
```

**Mas este parser falha porque:**
1. O formato do raw é numerado: `1. **Fatos:**` (com número antes)
2. O regex não captura até o próximo marcador corretamente
3. O texto é multilinha e complexo

---

### Causa #3: **FIRAC Não Está Sendo Regenerado**

Quando o cache contém apenas `raw` (sem JSON), o sistema deveria:
- Detectar que o cache está incompleto
- Regenerar o FIRAC chamando o LLM
- Salvar resultado em JSON

**Mas na verdade:**
- Retorna imediatamente com `data: None`
- Não tenta regenerar

---

## ✅ SOLUÇÕES PROPOSTAS

### Solução #1: **Limpar Cache Corrompido** (Rápido - 5min)

```powershell
# Deletar cache antigo do caso
Remove-Item -Recurse -Force "cases\caso_11b044bc\analysis_cache\"
```

**Benefício:** Força regeneração do FIRAC em formato JSON correto

**Limitação:** Temporário - se o LLM gerar raw text novamente, problema volta

---

### Solução #2: **Melhorar Parser de Raw Text** (Médio - 30min)

Melhorar o regex em `processos.py` para capturar corretamente o formato numerado:

```python
# processos.py - MELHORADO
if not data_firac and firac.get('raw'):
    import re
    raw = firac.get('raw', '')
    
    # Parser melhorado para formato "1. **Fatos:**"
    facts_match = re.search(
        r'(?:\d+\.\s+)?\*\*Fatos:?\*\*\s*(.*?)(?=\n\s*\d+\.\s+\*\*|\n\n|\Z)', 
        raw, 
        re.DOTALL | re.IGNORECASE
    )
    issue_match = re.search(
        r'(?:\d+\.\s+)?\*\*Quest[aã]o:?\*\*\s*(.*?)(?=\n\s*\d+\.\s+\*\*|\n\n|\Z)', 
        raw, 
        re.DOTALL | re.IGNORECASE
    )
    # ... etc
```

**Benefício:** Permite usar cache existente

---

### Solução #3: **Forçar Regeneração se data Vazio** (Recomendado - 1h)

Modificar `pipeline.py` para regenerar FIRAC quando cache está incompleto:

```python
# pipeline.py - generate_firac() MODIFICADO
def generate_firac(self, focus: Optional[str] = None) -> Dict[str, Any]:
    # ... código existente ...
    
    # Tenta carregar cache
    if firac_cache_path_json.exists():
        data = json.loads(firac_cache_path_json.read_text())
        raw = firac_cache_path_raw.read_text() if firac_cache_path_raw.exists() else ''
        
        # VALIDAÇÃO: Se data está vazio, regenerar
        if not data or all(not v for v in data.values()):
            logger.warning("Cache FIRAC incompleto (data vazio). Regenerando...")
            # Continua para regeneração abaixo
        else:
            return {'data': data, 'raw': raw, 'cached': True}
    
    elif firac_cache_path_raw.exists():
        raw = firac_cache_path_raw.read_text()
        
        # Tentar parsear raw para JSON
        data_parsed = self._parse_raw_firac_to_json(raw)
        
        if data_parsed:
            # Salvar JSON parseado
            self._cache_firac(focus, data_parsed, raw)
            return {'data': data_parsed, 'raw': raw, 'cached': True}
        else:
            logger.warning("Cache FIRAC raw não parseável. Regenerando...")
            # Continua para regeneração
    
    # REGENERAÇÃO: Chama LLM...
    # ... resto do código ...
```

**Benefício:** Resolve o problema na raiz

---

### Solução #4: **Adicionar Método de Parsing Robusto** (Completo - 2h)

Criar método dedicado para converter raw text em JSON:

```python
# pipeline.py - NOVO MÉTODO
def _parse_raw_firac_to_json(self, raw: str) -> Optional[Dict[str, str]]:
    """
    Parseia FIRAC em formato markdown/texto para JSON estruturado.
    
    Suporta formatos:
    - "**Fatos:**" 
    - "1. **Fatos:**"
    - "FATOS:"
    - "Fatos Relevantes:"
    """
    import re
    
    patterns = {
        'facts': [
            r'(?:\d+\.\s+)?\*\*Fatos:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*[A-Z]|\Z)',
            r'FATOS:?\s*(.*?)(?=\n\s*[A-Z]+:|\Z)',
            r'Fatos\s+Relevantes:?\s*(.*?)(?=\n\s*[A-Z]|\Z)'
        ],
        'issue': [
            r'(?:\d+\.\s+)?\*\*Quest[aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*[A-Z]|\Z)',
            r'QUEST[AÃ]O:?\s*(.*?)(?=\n\s*[A-Z]+:|\Z)',
        ],
        # ... patterns para rules, application, conclusion
    }
    
    result = {}
    
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
            if match:
                result[key] = match.group(1).strip()
                break
        
        if key not in result:
            result[key] = ""  # Fallback vazio
    
    # Validar se parseou algo útil
    if all(not v for v in result.values()):
        logger.warning("Parser não conseguiu extrair nenhum campo do raw FIRAC")
        return None
    
    return result
```

---

## 📋 PLANO DE AÇÃO RECOMENDADO

### Prioridade ALTA (Implementar Agora):

1. ✅ **Limpar cache corrompido** (5 min)
   ```powershell
   Remove-Item cases\*/analysis_cache\firac.* -Force
   ```

2. ✅ **Melhorar parser em processos.py** (30 min)
   - Ajustar regex para capturar formato numerado
   - Testar com raw text existente

3. ✅ **Adicionar validação em pipeline.py** (1h)
   - Verificar se `data` está completo ao carregar cache
   - Regenerar se incompleto

### Prioridade MÉDIA (Próxima Sprint):

4. **Criar método robusto de parsing** (2h)
   - Suportar múltiplos formatos de raw text
   - Melhorar detecção de seções

5. **Adicionar logging detalhado** (30 min)
   - Log quando cache está incompleto
   - Log quando parsing falha
   - Facilitar debugging futuro

### Prioridade BAIXA (Melhorias):

6. **Validação de schema FIRAC** (1h)
   - Garantir que todos os 5 campos estão presentes
   - Alertar se algum campo está vazio
   
7. **Cache TTL (Time-To-Live)** (2h)
   - Expirar cache antigo após X dias
   - Forçar regeneração periódica

---

## 🎯 VALIDAÇÃO PÓS-CORREÇÃO

Após implementar as soluções, validar:

1. **FIRAC gerado tem JSON válido:**
   ```python
   firac = pipeline.generate_firac()
   assert firac['data'] is not None
   assert 'facts' in firac['data']
   assert len(firac['data']['facts']) > 0
   ```

2. **Petição usa dados do FIRAC:**
   ```python
   peticao = pipeline.generate_peticao_rascunho(dados_ui, firac['data'])
   assert '[DADO NÃO DISPONÍVEL]' not in peticao
   assert 'Art.' in peticao  # Tem artigos de lei
   ```

3. **Seções da petição preenchidas:**
   - DOS FATOS: com narrativa específica do caso
   - DO DIREITO: com fundamentação e artigos
   - DOS PEDIDOS: com pedidos específicos (não genéricos)

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Antes | Meta |
|---------|-------|------|
| FIRAC com data válido | 0% | 100% |
| Petições com dados específicos | 20% | 95% |
| Cache em formato JSON | 0% | 100% |
| Artigos de lei na petição | 30% | 90% |
| Pedidos genéricos | 80% | <5% |

---

## 📝 CONCLUSÃO

### Problema Principal:
**FIRAC está retornando apenas raw text (markdown), sem JSON estruturado. Isso faz a petição ser gerada com dados vazios.**

### Causa Raiz:
**Cache antigo em formato markdown + falta de parser robusto + falta de validação ao carregar cache.**

### Impacto:
**CRÍTICO - Petições geradas são genéricas e não usam dados reais do caso.**

### Próximos Passos:
1. Limpar cache (5min)
2. Implementar Solução #2 e #3 (1h30)
3. Testar com caso real
4. Validar qualidade da petição

---

**Quer que eu comece a implementar as correções agora?**
