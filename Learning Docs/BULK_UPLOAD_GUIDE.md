# Guia de Upload em Massa de Processos

## Visão Geral

O recurso de **Upload em Massa** permite que você registre vários processos de uma só vez através de um arquivo CSV, economizando tempo na entrada de dados e permitindo importação em lote de clientes com múltiplos processos.

## Características

✅ **Interface Drag-and-Drop** - Arraste o arquivo CSV diretamente na zona de upload  
✅ **Preview Antes do Upload** - Visualize os dados antes de confirmar  
✅ **Validação Automática** - Detecção de erros no CSV  
✅ **Template CSV Baixável** - Obtenha um arquivo template com a estrutura correta  
✅ **Notificação por Email** - Receba relatório automático após o upload  
✅ **Tratamento de Erros** - Identifique problemas linha por linha  

---

## Como Usar

### 1. Acessar o Formulário de Upload

1. Na tela de gerenciamento de clientes, clique em um cliente
2. Procure pelo botão **"Upload em Massa de Processos"** ou navegue para:
   ```
   /processos/<id_cliente>/bulk-upload
   ```

### 2. Baixar o Template CSV

Clique no botão **"Baixar Template"** para obter um arquivo CSV pré-estruturado com exemplos.

**Estrutura do Template:**
```csv
nome_caso,numero_cnj,status,advogado_oab
"Cobrança de Débito","0000001-00.2025.1.00.0000","ATIVO","SP123456"
"Ação Indenizatória","0000002-00.2025.1.00.0000","PENDENTE","SP654321"
```

### 3. Preparar seu Arquivo CSV

#### Colunas Necessárias:

| Coluna | Obrigatório? | Descrição | Exemplo |
|--------|------------|-----------|---------|
| `nome_caso` | ✅ SIM | Nome/descrição do processo | "Cobrança de Débito" |
| `numero_cnj` | ⚠️ Opcional | Número CNJ do processo | "0000001-00.2025.1.00.0000" |
| `status` | ⚠️ Opcional | Status do processo | "ATIVO", "PENDENTE", "ENCERRADO" |
| `advogado_oab` | ⚠️ Opcional | OAB do advogado responsável | "SP123456" |

#### Requisitos Técnicos:

- **Formato**: CSV (separado por vírgula)
- **Codificação**: UTF-8
- **Cabeçalho**: Primeira linha deve conter os nomes das colunas
- **Tamanho máximo**: Recomenda-se não exceder 10.000 linhas por arquivo

#### Exemplo de Arquivo Válido:

```csv
nome_caso,numero_cnj,status,advogado_oab
"Cobrança de R$ 50.000","0000001-00.2025.1.00.0001","ATIVO","SP123456"
"Rescisão Contratual","0000002-00.2025.1.00.0002","ATIVO","SP654321"
"Indenização por Danos","0000003-00.2025.1.00.0003","PENDENTE","SP789012"
"Revisão de Aluguel","0000004-00.2025.1.00.0004","ENCERRADO",""
```

### 4. Fazer Upload do Arquivo

**Opção 1: Drag-and-Drop**
- Arraste o arquivo CSV para a zona azul de upload
- A zona mudará de cor indicando que o arquivo foi detectado

**Opção 2: Selecionar via Botão**
- Clique no botão "Selecionar Arquivo"
- Navegue até seu arquivo CSV

### 5. Visualizar Preview

Após selecionar o arquivo, um **preview** será exibido mostrando:
- Número total de linhas no CSV
- Primeiras 100 linhas para validação
- Todas as colunas do arquivo

**Revise os dados** para garantir que estão corretos antes de prosseguir.

### 6. Confirmar Upload

Clique no botão **"Upload de Processos"** para iniciar o processamento.

**Durante o upload:**
- Uma barra de progresso será exibida
- Não feche a página até a conclusão
- Aguarde o resultado final

### 7. Revisar Resultados

Após a conclusão, você verá:

#### ✅ Sucesso
- Número de processos criados com sucesso
- IDs dos processos criados
- Qualquer erro encontrado durante o processamento

#### ⚠️ Avisos
- Linhas com dados incompletos (colunas opcionais vazias)
- Advogados não encontrados no sistema

#### ❌ Erros
- Coluna `nome_caso` ausente ou vazia
- Arquivo não está em UTF-8
- Arquivo não é um CSV válido
- Advogado OAB com formato incorreto

---

## Validações Automáticas

O sistema valida automaticamente cada linha do CSV:

### ✓ Validações de Sucesso
- ✅ `nome_caso` não está vazio
- ✅ `numero_cnj` tem formato válido (se informado)
- ✅ `status` está em lista permitida (ATIVO, PENDENTE, ENCERRADO)
- ✅ `advogado_oab` existe no sistema (se informado)

### ⚠ Validações com Aviso
- ⚠️ Colunas opcionais vazias (processadas mesmo assim)
- ⚠️ Advogado não encontrado (processo criado sem advogado)

### ✗ Validações com Erro
- ❌ Arquivo não é CSV
- ❌ Arquivo não está em UTF-8
- ❌ Arquivo está vazio
- ❌ Colunas obrigatórias ausentes
- ❌ Linha sem dados essenciais

---

## Notificação por Email

### Configuração Necessária

Para usar a funcionalidade de notificação por email, configure as variáveis de ambiente:

```bash
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
EMAIL_FROM=noreply@advocacia-ia.local
SMTP_USE_TLS=true
```

### Enviar Relatório por Email

Após um upload bem-sucedido:
1. Clique em **"Enviar Relatório por Email"**
2. O email será enviado para o endereço cadastrado do cliente
3. O relatório incluirá:
   - Data e hora do upload
   - Cliente responsável
   - Número de processos criados
   - Lista dos IDs dos processos
   - Erros encontrados (se houver)

### Exemplo de Email Recebido

```
Subject: Upload em Massa de Processos - 25 processos criados

Prezado/a,

O upload em massa de processos foi concluído com sucesso!

Data/Hora: 16/10/2025 14:30:45
Cliente: Escritório de Advocacia XYZ
Processos Criados: 25

Detalhes dos Processos Criados:
- processo_001
- processo_002
- ... e mais 23 processos

Este é um email automático gerado pelo sistema Advocacia e IA.
```

---

## Exemplos Práticos

### Exemplo 1: Upload Simples (Apenas Nome do Caso)

```csv
nome_caso
"Cobrança de Débito"
"Rescisão Contratual"
"Indenização por Danos"
```

✅ Funcionará perfeitamente. Os outros campos serão deixados em branco.

### Exemplo 2: Upload com Advogados

```csv
nome_caso,advogado_oab
"Cobrança de Débito","SP123456"
"Ação Indenizatória","RJ654321"
"Revisão de Contrato",""
```

✅ Os dois primeiros terão advogado. O terceiro não.

### Exemplo 3: Upload com Status Diferentes

```csv
nome_caso,numero_cnj,status,advogado_oab
"Ativo agora","0000001-00.2025.1.00.0001","ATIVO","SP123456"
"Aguardando","0000002-00.2025.1.00.0002","PENDENTE","SP654321"
"Finalizado","0000003-00.2025.1.00.0003","ENCERRADO","SP789012"
```

✅ Três processos com status diferentes.

### Exemplo 4: Arquivo com Erro (Coluna Obrigatória Faltando)

```csv
numero_cnj,status
"0000001-00.2025.1.00.0001","ATIVO"
"0000002-00.2025.1.00.0002","PENDENTE"
```

❌ **Erro**: Coluna `nome_caso` é obrigatória e está faltando.

---

## Troubleshooting

### Problema: "Arquivo CSV não está em UTF-8"

**Solução:**
1. Abra o arquivo no Excel
2. Vá em **Arquivo > Salvar Como**
3. Selecione **"CSV (separado por vírgula)"** como tipo
4. Clique em **"Opções"** e escolha **UTF-8** como codificação

### Problema: "Coluna não reconhecida"

**Solução:**
- Verifique se o nome da coluna está correto
- Os nomes devem ser exatamente:
  - `nome_caso` (e não "nome caso" ou "name_case")
  - `numero_cnj` (e não "numeroCNJ" ou "numero_processo")
  - `status` (exatamente assim)
  - `advogado_oab` (e não "OAB_advogado")

### Problema: "Advogado não encontrado"

**Solução:**
- Verifique se o advogado está cadastrado no sistema
- Certifique-se de que a OAB está no formato correto (ex: "SP123456")
- Você pode deixar o campo em branco se o advogado não existir

### Problema: Preview está vazio

**Solução:**
- O arquivo pode estar em branco
- Verifique se o CSV tem dados além do cabeçalho
- Tente baixar o template e comparar o formato

### Problema: Upload muito lento

**Solução:**
- Se o arquivo tem mais de 5.000 linhas, divida em múltiplos uploads
- Recomenda-se máximo de 10.000 linhas por arquivo
- Verifique sua conexão de internet

---

## Endpoints da API

### 1. Download Template
```
GET /processos/api/<id_cliente>/bulk-upload/template
```
**Resposta:** Arquivo CSV baixável com estrutura e exemplos

### 2. Upload de Processos
```
POST /processos/api/<id_cliente>/bulk-upload
Content-Type: multipart/form-data

Body: csv_file (arquivo)
```

**Resposta de Sucesso (200):**
```json
{
  "status": "sucesso",
  "processos_criados": 25,
  "ids_criados": ["processo_001", "processo_002", ...],
  "erros": []
}
```

**Resposta com Erros (400):**
```json
{
  "status": "erro",
  "mensagem": "Arquivo CSV não está em UTF-8",
  "processos_criados": 0,
  "erros": []
}
```

### 3. Preview de Processos
```
POST /processos/api/<id_cliente>/bulk-upload/preview
Content-Type: multipart/form-data

Body: csv_file (arquivo)
```

**Resposta:**
```json
{
  "status": "sucesso",
  "total_linhas": 100,
  "colunas": ["nome_caso", "numero_cnj", "status", "advogado_oab"],
  "preview": [
    {"nome_caso": "Cobrança", "numero_cnj": "...", "status": "ATIVO", "advogado_oab": "SP123456"},
    ...
  ]
}
```

### 4. Enviar Notificação Email
```
POST /processos/api/<id_cliente>/bulk-upload/notify
Content-Type: application/json

Body:
{
  "processos_criados": 25,
  "ids_criados": ["id1", "id2", ...],
  "erros": ["erro1", "erro2", ...]
}
```

**Resposta:**
```json
{
  "status": "sucesso",
  "mensagem": "Email enviado para cliente@example.com"
}
```

---

## Boas Práticas

1. **Sempre faça preview** antes de confirmar upload
2. **Valide seus dados** antes de enviar o CSV
3. **Use a OAB correta** para evitar advogados não encontrados
4. **Faça backup** do seu arquivo CSV
5. **Divida uploads grandes** em múltiplos arquivos
6. **Teste com poucos registros** antes de fazer upload em massa
7. **Mantenha a codificação UTF-8** no arquivo CSV

---

## Suporte e Contato

Se encontrar problemas ou tiver dúvidas sobre o upload em massa:

1. Consulte esta documentação
2. Verifique os logs do sistema em `app/logs/`
3. Entre em contato com o suporte técnico

---

**Última atualização:** 16 de Outubro de 2025  
**Versão:** 1.0
