# 📊 CSV Import - Guia Rápido
## Importação em Massa de Processos

### 🎯 Acesso
**URL:** `/processos/<id_cliente>/bulk-upload`

### 📋 Campos Disponíveis

#### Obrigatórios
- `nome_caso` - Nome/descrição do processo

#### Opcionais - Básicos
- `numero_cnj` - Número CNJ (formato: 1234567-89.2023.8.26.0100)
- `status` - ATIVO, PENDENTE, ENCERRADO
- `advogado_oab` - OAB do advogado (ex: SP123456) - **DEIXAR VAZIO** se processo vindo de outro escritório
- `tipo_parte` - autor, reu, terceiro, reclamante, reclamada

> **💡 Lógica de Advogados:** Processos vindos de outros escritórios **NÃO** devem ter `advogado_oab` preenchido. O advogado será atribuído posteriormente no novo escritório. Deixe a coluna vazia nesses casos.

#### Opcionais - Detalhados (Item 1 - DIA 1)
- `comarca` - Comarca do processo (ex: São Paulo, Campinas)
- `vara` - Vara/Juizado (ex: 1ª Vara Cível)
- `juiz_nome` - Nome do juiz (ex: Dr. José Silva)
- `data_distribuicao` - Data distribuição (formato: YYYY-MM-DD)
- `data_citacao` - Data citação (formato: YYYY-MM-DD)
- `data_audiencia` - Data próxima audiência (formato: YYYY-MM-DD)
- `valor_causa` - Valor da causa em R$ (use ponto: 15000.50)
- `valor_condenacao` - Valor condenação em R$ (use ponto: 12000.00)
- `tipo_acao` - Tipo ação (ex: Cobrança, Indenização, Trabalhista)
- `grau_jurisdicao` - Grau (ex: 1º Grau, 2º Grau, STJ, STF)
- `instancia` - Instância (ex: Primeira Instância, Tribunal)
- `observacoes` - Observações adicionais

### 📝 Exemplo CSV Básico
```csv
nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Cobrança Débito",1234567-89.2023.8.26.0100,ATIVO,,autor
"Ação Indenizatória",2234567-89.2023.8.26.0200,PENDENTE,,reu
```

> **Nota:** Campo `advogado_oab` vazio - processos vindos de outro escritório serão criados sem advogado vinculado.

### 📝 Exemplo CSV Completo
```csv
nome_caso,numero_cnj,status,comarca,vara,juiz_nome,data_distribuicao,valor_causa,tipo_acao
"Cobrança",1234567-89.2023.8.26.0100,ATIVO,"São Paulo","1ª Vara Cível","Dr. José Silva",2023-05-15,15000.50,Cobrança
```

### 🔧 Funcionalidades

1. **Download Template**
   - Botão "Baixar Template" no formulário
   - Endpoint: `/processos/api/<id_cliente>/bulk-upload/template`
   - Retorna: `template_processos.csv` com todos os campos e linha de exemplo

2. **Preview**
   - Upload arquivo → Preview automático
   - Mostra até 100 linhas antes do upload definitivo
   - Validação de formato

3. **Upload**
   - Drag-and-drop ou seleção de arquivo
   - Validação UTF-8
   - Progresso visual
   - Relatório de erros linha a linha

4. **Resultado**
   - Quantidade de processos criados
   - Lista de IDs criados
   - Erros detalhados por linha
   - Opção de enviar relatório por email

### ⚠️ Validações

- **Encoding:** UTF-8 obrigatório
- **Extensão:** .csv obrigatório
- **Cabeçalho:** Deve conter `nome_caso`
- **advogado_oab:** Se preenchido, deve existir na tabela de advogados. Se vazio ou inexistente, processo criado sem vinculação
- **tipo_parte:** Apenas valores válidos (autor, reu, terceiro, reclamante, reclamada)
- **Valores numéricos:** Use ponto para decimal (15000.50 e não 15.000,50)
- **Datas:** Formato YYYY-MM-DD (2023-05-15)

### 📊 Endpoints API

| Método | URL | Descrição |
|--------|-----|-----------|
| GET | `/processos/<id>/bulk-upload` | Formulário HTML |
| POST | `/processos/api/<id>/bulk-upload` | Upload definitivo |
| POST | `/processos/api/<id>/bulk-upload/preview` | Preview antes upload |
| GET | `/processos/api/<id>/bulk-upload/template` | Download template |

### 🎯 Arquivos de Teste

- `test_csv_import_completo.csv` - 5 processos com TODOS os campos
- Inclui exemplos de:
  - Processo ativo com dados completos
  - Processo pendente
  - Processo encerrado
  - Ação trabalhista
  - Recurso de apelação

### 🚀 Workflow de Uso

1. Acesse `/processos/<id_cliente>/bulk-upload`
2. Clique "Baixar Template" para ter base
3. Preencha CSV com seus dados
4. Arraste arquivo ou clique "Selecionar Arquivo"
5. Aguarde preview carregar
6. Revise dados na tabela
7. Clique "Upload de Processos"
8. Aguarde processamento
9. Revise relatório de sucesso/erros

### ✅ Status da Implementação

- ✅ Método `bulk_create_processos_from_csv()` com 17 campos
- ✅ Endpoint POST `/api/<id>/bulk-upload`
- ✅ Endpoint POST `/api/<id>/bulk-upload/preview`
- ✅ Endpoint GET `/api/<id>/bulk-upload/template`
- ✅ Template HTML `bulk_upload_processos.html`
- ✅ Documentação completa na tabela
- ✅ Exemplos CSV básico e completo
- ✅ Arquivo de teste `test_csv_import_completo.csv`
- ✅ Validações de encoding, formato, tipos
- ✅ Relatório detalhado de erros linha a linha
- ✅ Integração com `CadastroManager`

---

**Item 4 do DIA 2:** ✅ **COMPLETO**

Criado: 13/11/2025
Status: 🟢 PRONTO PARA USO
