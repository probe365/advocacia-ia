# Documentação: Campo tipo_parte (Papel do Cliente no Processo)

## Visão Geral

O campo `tipo_parte` identifica o papel que o cliente (pessoa ou entidade representada) desempenha em um processo judicial. Este campo é **opcional** mas recomendado para uma melhor organização e análise dos processos.

## Valores Permitidos

### Processos Cíveis
- **`autor`** - Aquele que ajuíza a ação (pessoa ou entidade que promove a ação judicial)
- **`reu`** - Aquele contra quem a ação é proposta (pessoa ou entidade acusada)
- **`terceiro`** - Pessoa ou entidade envolvida no processo, mas não como autor ou réu principal

### Processos Trabalhistas
- **`reclamante`** - Aquele que faz a reclamação (geralmente o empregado)
- **`reclamada`** - Aquela contra quem a reclamação é feita (geralmente o empregador)

## Implementação Técnica

### Banco de Dados

#### Migração Alembic
Arquivo: `alembic/versions/0004_add_tipo_parte_to_processos.py`

A coluna `tipo_parte` foi adicionada à tabela `processos`:
- **Tipo**: VARCHAR(50)
- **Null**: Sim (opcional)
- **Índice**: `ix_processos_tipo_parte` para melhor performance em buscas
- **Default**: NULL

```sql
ALTER TABLE processos ADD COLUMN tipo_parte VARCHAR(50);
CREATE INDEX ix_processos_tipo_parte ON processos(tipo_parte);
```

### Backend

#### cadastro_manager.py

**Método `save_processo()`**
- Aceita `tipo_parte` no dicionário de dados
- Valida automaticamente valores antes de salvar
- Suporta atualização de processos existentes com `tipo_parte`

```python
dados_processo = {
    "id_cliente": "cliente_123",
    "nome_caso": "Cobrança de Débito",
    "numero_cnj": "1234567890123456789",
    "status": "ATIVO",
    "advogado_oab": "SP123456",
    "tipo_parte": "autor"  # Novo campo
}
proc_id = manager.save_processo(dados_processo)
```

**Método `bulk_create_processos_from_csv()`**
- Valida `tipo_parte` para cada linha do CSV
- Retorna erros detalhados para valores inválidos
- Normaliza valores para minúsculas antes de salvar

#### Validação de tipo_parte

Valores válidos (case-insensitive):
```python
valid_tipos = {"autor", "reu", "terceiro", "reclamante", "reclamada"}
```

Se um valor inválido for fornecido no CSV:
```
Linha 5: tipo_parte inválido. Valores válidos: autor, reu, terceiro, reclamante, reclamada
```

### Frontend

#### bulk_upload_processos.html

**Tabela de Referência**
O formulário exibe uma tabela com todas as colunas aceitas, incluindo `tipo_parte`:

| Coluna | Obrigatório | Descrição |
|--------|-------------|-----------|
| nome_caso | ✓ SIM | Nome do processo |
| numero_cnj | Opcional | Número CNJ |
| status | Opcional | ATIVO/PENDENTE/ENCERRADO |
| advogado_oab | Opcional | OAB do advogado |
| tipo_parte | **Opcional** | **autor, reu, terceiro, reclamante, reclamada** |

**Exemplo CSV Atualizado**
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Cobrança de Débito",123456789012345678,ATIVO,SP123456,autor
"Ação Indenizatória",223456789012345679,PENDENTE,SP654321,reu
"Recuperação de Crédito",323456789012345680,ATIVO,SP789012,terceiro
```

#### Utilidades tipo_parte_helpers.py

Funções de formatação e validação:

```python
from app.utils.tipo_parte_helpers import *

# Obter rótulo em português
get_tipo_parte_label('autor')  # Retorna: 'Autor'

# Obter descrição
get_tipo_parte_description('reu')  # Retorna: 'Aquele contra quem a ação é proposta...'

# Obter classe Bootstrap para badge
get_tipo_parte_badge_class('reclamante')  # Retorna: 'badge-info'

# Obter ícone Font Awesome
get_tipo_parte_icon('autor')  # Retorna: 'fa-gavel'

# Validar valor
validate_tipo_parte('autor')  # Retorna: True
validate_tipo_parte('invalido')  # Retorna: False

# Formatar para exibição em templates
format_tipo_parte_for_display('reu')
# Retorna: <span class="badge badge-danger"><i class="fas fa-shield-alt"></i> Réu</span>

# Obter tipos por categoria
get_tipos_parte_by_category('civil')   # Retorna: ['autor', 'reu', 'terceiro']
get_tipos_parte_by_category('trabalhista')  # Retorna: ['reclamante', 'reclamada']
```

## Fluxo de Uso

### 1. Upload em Massa (CSV)

Passos:
1. Navegar para: `/processos/<id_cliente>/bulk-upload`
2. Arrastar ou selecionar arquivo CSV
3. Visualizar preview dos processos
4. Confirmar upload

Validações:
- ✓ `nome_caso` é obrigatório
- ✓ `tipo_parte` é validado contra valores permitidos
- ✓ Erros de validação aparecem em detalhes por linha

### 2. Criação Individual

Quando criar um processo via formulário único:
1. Preencher dados básicos (nome_caso, etc.)
2. **Selecionar tipo_parte** (dropdown com opções)
3. Confirmar criação

### 3. Edição de Processo

Para atualizar tipo_parte de um processo existente:
1. Abrir processo
2. Editar campo `tipo_parte`
3. Salvar alterações

## Exemplos de Uso

### Exemplo 1: Processo Cível com Cliente como Autor
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"João Silva x Empresa XYZ",1234567890123456789,ATIVO,SP123456,autor
```

**Interpretação**: O cliente é o autor (quem ajuizou a ação contra a Empresa XYZ)

### Exemplo 2: Processo Trabalhista
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Reclamação Trabalhista",9876543210987654321,PENDENTE,SP654321,reclamante
```

**Interpretação**: O cliente é o reclamante (empregado) em uma reclamação trabalhista

### Exemplo 3: Terceiro em Ação Coletiva
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Ação Civil Pública",5555666677778888999,ATIVO,SP789012,terceiro
```

**Interpretação**: O cliente é terceiro interessado em uma ação coletiva

## Impacto nos Relatórios e Análise

Com o `tipo_parte` preenchido, é possível:

### 1. Filtrar Processos por Tipo de Parte
- Mostrar apenas processos onde cliente é **autor**
- Mostrar apenas processos onde cliente é **réu**
- Etc.

### 2. Análise de Carteira
- Percentual de processos por tipo de parte
- Gráfico de distribuição (autor vs réu vs terceiro)
- Taxa de sucesso/derrota por tipo de parte

### 3. Relatórios Estratégicos
- Casos defensivos (ação contra o cliente)
- Casos agressivos (cliente move ação)
- Casos auxiliares (cliente como terceiro)

### 4. Integração com IA (Pipeline)
- FIRAC pode ser customizado conforme tipo_parte
- Análise de riscos diferenciada para cada papel
- Petições geradas com perspectiva correta (autor vs ré u)

## Migração de Dados Existentes

Se você tem processos já cadastrados sem `tipo_parte`:

### Opção 1: Deixar vazio (Compatível com Versões Antigas)
```sql
-- Nenhuma ação necessária, campo permanece NULL
SELECT * FROM processos WHERE tipo_parte IS NULL;
```

### Opção 2: Inferir Automaticamente (Script Python)
```python
from cadastro_manager import CadastroManager
from app.utils.tipo_parte_helpers import TIPO_PARTE_BY_CATEGORY

manager = CadastroManager()

# Exemplo: Inferir que processos antigos são de defesa (reu)
processos = manager._execute_query(
    "SELECT id_processo FROM processos WHERE tipo_parte IS NULL",
    fetch="all"
)

for proc in processos:
    # Lógica customizada para inferir tipo_parte
    tipo_parte = infer_tipo_parte(proc)  # Sua lógica aqui
    manager.save_processo({
        'id_processo': proc['id_processo'],
        'tipo_parte': tipo_parte
    }, id_processo=proc['id_processo'])
```

### Opção 3: Importação via CSV
Usar a funcionalidade de bulk upload para importar `tipo_parte` para processos existentes.

## Considerações de Design

### Por que tipo_parte é opcional?

1. **Compatibilidade Reversa**: Processos já cadastrados continuam funcionando
2. **Flexibilidade**: Alguns clientes podem não precisar desta informação
3. **Gradual Adoption**: Equipe pode começar a usar em novos processos
4. **Dados Públicos**: Alguns processos (públicos) podem não precisar desta classificação

### Campos Relacionados

- `id_cliente`: Quem é a parte (pessoa/entidade)
- `tipo_parte`: Qual o papel dessa parte no processo
- `advogado_oab`: Quem a representa
- `id_escritorio`: Qual escritório a representa

## Troubleshooting

### Problema: CSV com tipo_parte inválido é rejeitado
**Solução**: Validar valores contra a lista permitida antes de enviar

### Problema: tipo_parte não aparece em relatórios antigos
**Solução**: Usar JOIN com LEFT para permitir valores NULL nos relatórios

### Problema: Integração com IA não reconhece tipo_parte
**Solução**: Atualizar pipeline.py para ler tipo_parte do banco de dados

## Próximos Passos

1. ✅ Alembic Migration criada
2. ✅ Backend atualizado (cadastro_manager.py)
3. ✅ CSV Bulk Upload suporta tipo_parte
4. ⏳ Formulários de UI devem adicionar dropdown tipo_parte
5. ⏳ Relatórios devem exibir tipo_parte
6. ⏳ Pipeline de IA deve usar tipo_parte para customizar análises

## Referências

- Tipos de Partes Judiciais (CNJ): https://www.cnj.jus.br/
- Resolução CNJ nº 65/2008: Uniformização de nomenclatura
- Lei de Acesso à Informação: Transparência em Processos Judiciais
