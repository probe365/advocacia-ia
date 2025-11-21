# Summary: Implementação do Campo tipo_parte

## Objetivo
Identificar o papel do cliente em cada processo judicial (se é autor, réu, terceiro, reclamante ou reclamada).

## Mudanças Implementadas

### 1. Database Migration ✅
**Arquivo**: `alembic/versions/0004_add_tipo_parte_to_processos.py`
- Adiciona coluna `tipo_parte` (VARCHAR(50), nullable) à tabela `processos`
- Cria índice `ix_processos_tipo_parte` para melhor performance
- Suporta downgrade (reversível)

### 2. Backend - cadastro_manager.py ✅

#### Método: `save_processo()`
- **Antes**: Não suportava `tipo_parte`
- **Depois**: Aceita e valida `tipo_parte` em INSERT e UPDATE
- **Mudança**: Adicionado parâmetro `tipo_parte` às queries SQL

#### Método: `bulk_create_processos_from_csv()`
- **Antes**: Aceitava 4 colunas (nome_caso, numero_cnj, status, advogado_oab)
- **Depois**: Aceita 5 colunas (adicionado `tipo_parte`)
- **Validação**: Valida valores contra {autor, reu, terceiro, reclamante, reclamada}
- **Erro Handling**: Retorna erro por linha se `tipo_parte` for inválido
- **Normalização**: Converte para minúsculas antes de salvar

### 3. Frontend - bulk_upload_processos.html ✅
- Adicionada coluna `tipo_parte` à tabela de referência
- Atualizado exemplo CSV para incluir `tipo_parte`
- Labels explicam papéis: "autor, reu, terceiro, reclamante, reclamada"
- Preview table automaticamente exibe a coluna se presente no CSV

### 4. Utilidades - tipo_parte_helpers.py ✅
**Arquivo**: `app/utils/tipo_parte_helpers.py`

Funções disponíveis:
- `get_tipo_parte_label()` - Rótulo em português
- `get_tipo_parte_description()` - Descrição detalhada
- `get_tipo_parte_badge_class()` - Classe CSS Bootstrap para badge
- `get_tipo_parte_icon()` - Ícone Font Awesome
- `validate_tipo_parte()` - Valida valor
- `format_tipo_parte_for_display()` - HTML formatado para templates
- `get_tipos_parte_by_category()` - Filtra por categoria (civil/trabalhista)

**Constantes**:
```python
VALID_TIPOS_PARTE = {'autor', 'reu', 'terceiro', 'reclamante', 'reclamada'}

TIPO_PARTE_LABELS = {
    'autor': 'Autor',
    'reu': 'Réu',
    'terceiro': 'Terceiro',
    'reclamante': 'Reclamante',
    'reclamada': 'Reclamada',
}

TIPO_PARTE_BY_CATEGORY = {
    'civil': ['autor', 'reu', 'terceiro'],
    'trabalhista': ['reclamante', 'reclamada'],
    'todas': ['autor', 'reu', 'terceiro', 'reclamante', 'reclamada'],
}
```

### 5. Documentação ✅
**Arquivo**: `TIPO_PARTE_DOCUMENTATION.md`

Inclui:
- Visão geral do campo
- Valores permitidos com descrições
- Implementação técnica (BD, backend, frontend)
- Fluxos de uso
- Exemplos de CSV
- Impacto em relatórios e análise
- Estratégia de migração de dados
- Troubleshooting

## Fluxo de Uso Passo-a-Passo

### Upload em Massa (Novo)
1. Navegar para `/processos/<id_cliente>/bulk-upload`
2. Preparar CSV com coluna `tipo_parte` (opcional):
   ```csv
   nome_caso,numero_cnj,status,advogado_oab,tipo_parte
   "Cobrança",123456789012345678,ATIVO,SP123456,autor
   "Indenização",223456789012345679,PENDENTE,SP654321,reu
   ```
3. Arrastar ou selecionar arquivo
4. Visualizar preview
5. Confirmar upload

### Validações Automáticas
- ✅ `nome_caso` obrigatório
- ✅ `tipo_parte` validado se fornecido
- ✅ Erros listados por linha
- ✅ Processos válidos criados mesmo com algumas linhas com erro

### Exemplo de Erro
```json
{
  "status": "sucesso",
  "processos_criados": 2,
  "erros": [
    "Linha 5: tipo_parte inválido. Valores válidos: autor, reu, terceiro, reclamante, reclamada"
  ],
  "ids_criados": ["caso_abc12345", "caso_def67890"]
}
```

## Compatibilidade

✅ **Compatível com versões antigas**
- Campo é NULLABLE
- Processos existentes continuam funcionando
- Não afeta comportamento se `tipo_parte` não for fornecido
- Migrations são reversíveis (downgrade disponível)

## Proximos Passos Recomendados

### Curto Prazo
1. [ ] Executar migration: `alembic upgrade head`
2. [ ] Testar bulk upload com CSV incluindo `tipo_parte`
3. [ ] Validar dados salvos corretamente no banco

### Médio Prazo
4. [ ] Adicionar dropdown `tipo_parte` ao formulário de novo processo
5. [ ] Adicionar campo editável em visualização de processo
6. [ ] Criar filtro de listagem por `tipo_parte`

### Longo Prazo
7. [ ] Integrar `tipo_parte` ao pipeline de análise IA
8. [ ] Criar relatórios com distribuição por tipo de parte
9. [ ] Customizar FIRAC conforme papel do cliente
10. [ ] Validar recomendações estratégicas por tipo de parte

## Testes Recomendados

```bash
# Test 1: CSV com tipo_parte válido
teste_upload_csv_com_tipo_parte_valido()

# Test 2: CSV com tipo_parte inválido
teste_upload_csv_com_tipo_parte_invalido()

# Test 3: CSV sem coluna tipo_parte (backward compat)
teste_upload_csv_sem_tipo_parte()

# Test 4: Editar tipo_parte de processo existente
teste_editar_tipo_parte()

# Test 5: Query por tipo_parte
teste_query_por_tipo_parte()
```

## Arquivos Modificados

```
c:\adv-IA-F\
├── alembic/versions/
│   └── 0004_add_tipo_parte_to_processos.py         [NOVO]
├── app/
│   ├── utils/
│   │   └── tipo_parte_helpers.py                   [NOVO]
│   └── blueprints/
│       └── processos.py                            [SEM MUDANÇAS - pronto para expansão]
├── templates/
│   └── bulk_upload_processos.html                  [ATUALIZADO]
├── cadastro_manager.py                             [ATUALIZADO]
└── TIPO_PARTE_DOCUMENTATION.md                     [NOVO]
```

## Verificação Rápida

```python
# 1. Verificar migração
# Run: alembic upgrade head
# Result: Coluna tipo_parte criada em processos

# 2. Verificar backend
from cadastro_manager import CadastroManager
manager = CadastroManager()
proc = manager.save_processo({
    'id_cliente': 'test_client',
    'nome_caso': 'Test',
    'tipo_parte': 'autor'
})
# Result: Deve salvar sem erro

# 3. Verificar helpers
from app.utils.tipo_parte_helpers import *
get_tipo_parte_label('reu')  # Retorna: 'Réu'
validate_tipo_parte('autor')  # Retorna: True
# Result: Funções funcionam corretamente

# 4. Verificar CSV upload
# Upload CSV com coluna tipo_parte
# Result: Deve processar e validar corretamente
```

## Questions & Support

Para dúvidas sobre implementação ou uso:
- Consultar `TIPO_PARTE_DOCUMENTATION.md` para detalhes técnicos
- Verificar constantes em `app/utils/tipo_parte_helpers.py`
- Revisar exemplos de CSV em `bulk_upload_processos.html`
