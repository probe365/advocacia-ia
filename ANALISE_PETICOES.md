# 📄 Análise de Petições - Tipos Prioritários
## Advocacia e IA | Item 9 - Múltiplos Tipos de Petições

**Data de Criação:** 11/11/2025  
**PDFs Analisados:** 
- `Peticoes Área Civil.pdf`
- `Peticoes Trabalhistas.pdf`  
**Objetivo:** Definir 2-3 tipos prioritários para MVP (28/11)  
**Status:** 📊 ANÁLISE COMPLETA

---

## 📋 ÍNDICE

1. [Contexto e Objetivos](#contexto-e-objetivos)
2. [Petição Inicial (Já Implementada)](#petição-inicial-já-implementada)
3. [Análise: Contestação (Civil)](#análise-contestação-civil)
4. [Análise: Reclamação Trabalhista](#análise-reclamação-trabalhista)
5. [Análise: Réplica (Civil)](#análise-réplica-civil)
6. [Análise: Recurso de Apelação](#análise-recurso-de-apelação)
7. [Recomendação de Prioridades](#recomendação-de-prioridades)
8. [Especificação Técnica - Contestação](#especificação-técnica-contestação)
9. [Especificação Técnica - Reclamação Trabalhista](#especificação-técnica-reclamação-trabalhista)
10. [Implementação - Roadmap](#implementação-roadmap)

---

## 🎯 CONTEXTO E OBJETIVOS

### Objetivo do Item 9:
> "Permitir geração de **múltiplos tipos de petições** além da Petição Inicial (já implementada), utilizando RAG e LangChain para garantir qualidade e personalização."

### Critérios de Priorização:
1. **Frequência de Uso:** Petições mais comuns no dia a dia do advogado
2. **Complexidade Técnica:** Equilíbrio entre valor entregue e esforço de implementação
3. **Diferenciação Competitiva:** Tipos que agregam mais valor ao SaaS
4. **Compatibilidade com RAG:** Petições que se beneficiam de contexto documental
5. **Prazo MVP:** Viável implementar até 28/11 (2-3 tipos)

### Tipos de Petições Identificados nos PDFs:

**Área Civil:**
- Petição Inicial (✅ Implementada)
- Contestação
- Réplica
- Reconvenção
- Recurso de Apelação
- Agravo de Instrumento
- Embargos de Declaração
- Impugnação ao Cumprimento de Sentença
- Exceção de Pré-executividade

**Área Trabalhista:**
- Reclamação Trabalhista (Inicial)
- Contestação Trabalhista
- Recurso Ordinário
- Recurso de Revista
- Agravo de Petição
- Embargos à Execução

---

## ✅ PETIÇÃO INICIAL (JÁ IMPLEMENTADA)

### Estrutura Atual:
```
1. Endereçamento (Juízo, Vara)
2. Qualificação das Partes (Autor e Réu)
3. DOS FATOS
4. DO DIREITO
5. DOS PEDIDOS
6. Valor da Causa
7. Provas
8. Data e Assinatura
```

### Campos de Entrada (UI):
- Advogado(a) (dropdown)
- Cliente (dropdown - autor)
- Parte adversa (dropdown - réu)
- Pedidos Principais (textarea)
- Valor da Causa (number)
- Vara/Juízo (dropdown)

### Dados Utilizados:
- **FIRAC Analysis:** Facts, Issue, Rule, Application, Conclusion
- **Documentos do Processo:** (via RAG)
- **KB Global:** Jurisprudência, modelos

### Status: ✅ **FUNCIONAL** - Gera petições completas e personalizadas

---

## 🥈 ANÁLISE: CONTESTAÇÃO (CIVIL)

### O que é:
Resposta do réu à petição inicial, apresentando sua defesa e contrariando os argumentos do autor.

### Frequência de Uso: ⭐⭐⭐⭐⭐
- **Altíssima:** Praticamente todo processo tem contestação
- Essencial para advogados que atuam na defesa

### Estrutura Típica:
```
1. Endereçamento
2. Qualificação das Partes (Contestante/Autor)
3. PRELIMINARES (se houver)
   - Ilegitimidade passiva
   - Falta de interesse de agir
   - Inépcia da inicial
   - Incompetência do juízo
4. DO MÉRITO
   - Impugnação aos fatos narrados
   - Impugnação aos valores
   - Provas da versão do réu
   - Jurisprudência favorável
5. DA LITIGÂNCIA DE MÁ-FÉ (se aplicável)
6. DAS PROVAS
   - Documentos em anexo
   - Provas a produzir (testemunhal, pericial)
7. DOS PEDIDOS
   - Acolhimento das preliminares
   - Improcedência do pedido
   - Condenação do autor em custas
8. Valor da Causa (impugnar se discordar)
9. Data e Assinatura
```

### Campos de Entrada Necessários (UI):

**Básicos:**
- [ ] Advogado(a) (dropdown)
- [ ] Cliente Contestante (= Réu) (dropdown)
- [ ] Processo (dropdown - busca petição inicial)

**Estratégia:**
- [ ] Preliminares (checkboxes):
  * Ilegitimidade passiva
  * Falta de interesse de agir
  * Inépcia da inicial
  * Incompetência do juízo
  * Prescrição/Decadência
  * Coisa julgada
- [ ] Argumentos de Mérito (textarea - editor rico)
- [ ] Impugnar Valor da Causa? (checkbox + novo valor)
- [ ] Litigância de Má-Fé? (checkbox + justificativa)

**Provas:**
- [ ] Documentos em Anexo (upload múltiplo)
- [ ] Provas a Produzir (checkboxes):
  * Prova testemunhal (+ quantidade de testemunhas)
  * Prova pericial (+ tipo de perícia)
  * Depoimento pessoal do autor
  * Inspeção judicial

**Pedidos:**
- [ ] Pedidos Principais (textarea)

### Dados Utilizados pelo RAG:

**Do Processo:**
- ✅ Petição Inicial completa (extrair argumentos do autor)
- ✅ FIRAC Analysis (compreender posição do autor)
- ✅ Documentos anexos à inicial (identificar pontos fracos)
- ✅ Jurisprudência contrária ao autor

**Da KB Global:**
- ✅ Modelos de contestação similares
- ✅ Jurisprudência favorável ao réu
- ✅ Teses de defesa comuns para a área

**Do Cliente:**
- ✅ Documentos que provam versão do réu
- ✅ Contratos, emails, comprovantes

### Complexidade de Implementação: 🟡 **MÉDIA**

**Desafios:**
- Precisa ler e interpretar a petição inicial do processo
- RAG deve buscar jurisprudência **CONTRÁRIA** aos argumentos do autor
- Geração de argumentos de defesa (não apenas repetir fatos)

**Vantagens:**
- Reutiliza estrutura existente (FIRAC, RAG, LangChain)
- Diferencial competitivo: poucos apps geram contestação automaticamente
- Alto valor para escritórios de defesa

### Estimativa de Esforço: **16-24 horas**
- Prompt LangChain específico: 4-6h
- UI do formulário: 3-4h
- Integração RAG (buscar petição inicial): 4-6h
- Lógica de preliminares: 3-4h
- Testes: 2-4h

---

## 🥉 ANÁLISE: RECLAMAÇÃO TRABALHISTA

### O que é:
Petição inicial no âmbito trabalhista, com estrutura própria e linguagem específica da Justiça do Trabalho.

### Frequência de Uso: ⭐⭐⭐⭐⭐
- **Altíssima:** Escritórios que atuam em trabalhista fazem dezenas por mês
- Diferente da petição inicial cível (tem particularidades)

### Estrutura Típica:
```
1. Endereçamento (Vara do Trabalho)
2. RECLAMANTE (empregado)
   - Qualificação completa
   - Endereço, CPF, RG, PIS
   - Benefícios da gratuidade (se aplicável)
3. RECLAMADA (empregador)
   - Qualificação (razão social, CNPJ)
   - Endereço completo
4. SÍNTESE DOS FATOS
   - Admissão e demissão (datas)
   - Função exercida
   - Salário e jornada
   - Rescisão (demissão sem justa causa, etc)
   - Verbas não pagas
5. DIREITOS LESADOS
   - Horas extras não pagas
   - Adicional noturno
   - Férias vencidas + 1/3
   - 13º salário
   - FGTS + 40%
   - Aviso prévio
   - Danos morais (assédio, condições insalubres)
6. FUNDAMENTO LEGAL
   - CLT
   - Súmulas TST
   - Jurisprudência trabalhista
7. DOS PEDIDOS
   - Reconhecimento de vínculo (se aplicável)
   - Pagamento de verbas rescisórias
   - Indenizações
   - Multas (art. 467, 477 CLT)
8. VALOR DA CAUSA
9. PROVAS
   - Testemunhal (máx 3 testemunhas)
   - Documental
   - Pericial (insalubridade, periculosidade)
10. REQUERIMENTOS FINAIS
    - Intimação do INSS (se pedir aposentadoria)
    - Citação da reclamada
    - Condenação em honorários
11. Data e Assinatura
```

### Campos de Entrada Necessários (UI):

**Qualificação do Reclamante:**
- [ ] Cliente (dropdown)
- [ ] PIS/PASEP (input)
- [ ] Beneficiário da Justiça Gratuita? (checkbox)

**Qualificação da Reclamada:**
- [ ] Parte Adversa (dropdown)
- [ ] CNPJ (auto-preencher da parte adversa)

**Dados do Contrato:**
- [ ] Data de Admissão (date)
- [ ] Data de Demissão (date)
- [ ] Função/Cargo (input)
- [ ] Último Salário (number)
- [ ] Tipo de Jornada (dropdown):
  * 44h semanais
  * 40h semanais
  * 8h diárias
  * 6h diárias (bancário)
  * 12x36 (plantão)
- [ ] Tipo de Rescisão (dropdown):
  * Demissão sem justa causa
  * Demissão por justa causa (impugnar)
  * Pedido de demissão
  * Rescisão indireta
  * Término de contrato temporário

**Verbas Reclamadas (checkboxes):**
- [ ] Aviso prévio
- [ ] 13º salário proporcional
- [ ] Férias vencidas + 1/3
- [ ] Férias proporcionais + 1/3
- [ ] Saldo de salário
- [ ] FGTS + 40% (multa)
- [ ] Seguro-desemprego (guias)
- [ ] Horas extras (+ média mensal)
- [ ] Adicional noturno
- [ ] Adicional de insalubridade
- [ ] Adicional de periculosidade
- [ ] Reflexos (DSR, 13º, férias, FGTS)
- [ ] Danos morais (+ valor estimado)
- [ ] Danos materiais (+ valor)

**Detalhes Específicos:**
- [ ] Horas Extras? (checkbox):
  * Média mensal de horas extras (number)
  * Percentual (50%, 100%)
- [ ] Danos Morais? (checkbox):
  * Descrição do dano (textarea)
  * Valor estimado (number)
- [ ] Insalubridade/Periculosidade? (checkbox):
  * Tipo (dropdown: insalubridade grau máximo/médio/mínimo, periculosidade)
  * Perícia necessária

**Provas:**
- [ ] Documentos em Anexo (upload: CTPS, recibos, contracheques, etc)
- [ ] Testemunhas (máx 3):
  * Nome completo
  * Qualificação
  * Endereço

### Dados Utilizados pelo RAG:

**Do Cliente:**
- ✅ CTPS digitalizada (OCR para extrair dados)
- ✅ Contracheques (calcular médias)
- ✅ Termo de rescisão (TRCT)
- ✅ Mensagens de WhatsApp (provar assédio)
- ✅ Fotos do local de trabalho (insalubridade)

**Da KB Global:**
- ✅ Modelos de reclamação trabalhista
- ✅ Jurisprudência TST (Súmulas, OJ)
- ✅ Cálculos de verbas rescisórias (tabelas)
- ✅ Teses de dano moral (valores médios)

### Complexidade de Implementação: 🟡 **MÉDIA-ALTA**

**Desafios:**
- Formulário extenso (muitos campos específicos)
- Cálculos de verbas trabalhistas (complexos)
- Conhecimento específico CLT + TST
- OCR de documentos (CTPS, contracheques) - OPCIONAL

**Vantagens:**
- Muito demandado por escritórios trabalhistas
- Diferenciais: cálculo automático de verbas
- RAG pode sugerir teses comuns (horas extras, dano moral)

### Estimativa de Esforço: **20-28 horas**
- Prompt LangChain específico: 6-8h
- UI do formulário (extenso): 5-7h
- Lógica de cálculo de verbas: 4-6h
- Integração RAG (documentos trabalhistas): 3-5h
- Testes: 2-4h

---

## 🥉 ANÁLISE: RÉPLICA (CIVIL)

### O que é:
Resposta do autor à contestação do réu, refutando os argumentos de defesa.

### Frequência de Uso: ⭐⭐⭐⭐
- **Alta:** Após toda contestação, pode ter réplica
- Importante para processos contenciosos

### Estrutura Típica:
```
1. Endereçamento
2. Qualificação das Partes
3. RECHAÇO ÀS PRELIMINARES
   - Refutar ilegitimidade
   - Refutar falta de interesse
   - Manter competência do juízo
4. REAFIRMAÇÃO DO MÉRITO
   - Contestar versão do réu
   - Reforçar argumentos da inicial
   - Contraditar provas do réu
5. IMPUGNAÇÃO AO VALOR DA CAUSA (se réu impugnou)
6. DOS PEDIDOS
   - Rejeição das preliminares
   - Procedência do pedido inicial
7. Data e Assinatura
```

### Complexidade: 🟡 **MÉDIA**
- Similar à contestação (resposta a uma peça)
- Reutiliza estrutura da inicial + argumentos da contestação

### Estimativa de Esforço: **12-18 horas**

### Prioridade para MVP: 🟠 **BAIXA**
- Menos urgente que contestação e reclamação trabalhista
- Pode ser deixada para Fase 2

---

## 🏆 ANÁLISE: RECURSO DE APELAÇÃO

### O que é:
Recurso contra sentença de 1º grau, direcionado ao Tribunal de Justiça.

### Frequência de Uso: ⭐⭐⭐⭐
- **Alta:** Comum quando há sucumbência

### Estrutura Típica:
```
1. Endereçamento (Juízo a quo)
2. Qualificação das Partes (Apelante/Apelado)
3. SÍNTESE DO PROCESSO
4. DA SENTENÇA RECORRIDA
5. DAS RAZÕES DO RECURSO
   - Questões de fato (prova mal valorada)
   - Questões de direito (erro de interpretação)
   - Divergência jurisprudencial
6. DO PEDIDO
   - Provimento do recurso
   - Reforma da sentença
7. Data e Assinatura
```

### Complexidade: 🔴 **ALTA**
- Requer análise profunda da sentença
- Identificar erros do juiz (complexo para IA)
- Busca jurisprudencial sofisticada

### Estimativa de Esforço: **28-36 horas**

### Prioridade para MVP: 🟠 **BAIXA**
- Muito complexo para MVP
- Deixar para Fase 2 ou versão futura

---

## 🎯 RECOMENDAÇÃO DE PRIORIDADES

### Para MVP (28/11) - 2 Tipos Além da Inicial:

| Tipo | Prioridade | Esforço | Valor | Justificativa |
|------|-----------|---------|-------|---------------|
| **Contestação (Civil)** | 🥇 **ALTA** | 16-24h | ⭐⭐⭐⭐⭐ | Essencial para defesa, alta frequência, diferencial competitivo |
| **Reclamação Trabalhista** | 🥈 **ALTA** | 20-28h | ⭐⭐⭐⭐⭐ | Mercado específico (escritórios trabalhistas), muito demandado |
| Réplica (Civil) | 🥉 Média | 12-18h | ⭐⭐⭐⭐ | Útil mas menos urgente, pode esperar Fase 2 |
| Recurso de Apelação | 🥉 Baixa | 28-36h | ⭐⭐⭐ | Muito complexo, melhor em V2.0 com IA mais sofisticada |

### Decisão Estratégica:

**FASE 1 (MVP - 28/11):**
1. ✅ Petição Inicial (já implementada)
2. 🆕 **Contestação (Civil)** - Implementar na Semana 5 (09-10/12)
3. 🆕 **Reclamação Trabalhista** - Implementar na Semana 5 (10-11/12)

**Total estimado:** 36-52h (2 devs + Paulo = 9-13h por pessoa em 3 dias)

**FASE 2 (Pós-28/11, até 15/12):**
4. Réplica (Civil) - Opcional se sobrar tempo
5. Contestação Trabalhista - Complemento natural da Reclamação

**FUTURO (V2.0 - 2025):**
- Recurso de Apelação
- Agravo de Instrumento
- Embargos de Declaração
- Impugnação ao Cumprimento

---

## 🔧 ESPECIFICAÇÃO TÉCNICA - CONTESTAÇÃO

### Prompt LangChain:

```python
CONTESTACAO_PROMPT = PromptTemplate(
    input_variables=[
        "advogado_nome",
        "advogado_oab",
        "cliente_nome",  # Réu/Contestante
        "cliente_qualificacao",
        "autor_nome",  # Autor da inicial
        "processo_numero",
        "vara_juizo",
        "comarca",
        "peticao_inicial_completa",  # 📄 RAG busca
        "firac_analise",  # 📊 Pipeline analysis
        "preliminares_selecionadas",  # Lista
        "argumentos_merito",  # Textarea do usuário
        "impugnacao_valor_causa",  # Boolean + novo valor
        "litigancia_ma_fe",  # Boolean + justificativa
        "documentos_anexos",  # Lista de arquivos
        "provas_a_produzir",  # Lista (testemunhal, pericial, etc)
        "pedidos_principais",
        "jurisprudencia_favoravel",  # 📚 RAG busca
        "modelos_contestacao_similares"  # 📚 RAG busca
    ],
    template="""
Você é um advogado especializado em direito civil brasileiro, com vasta experiência em defesa processual.

## CONTEXTO DO CASO:
- Processo nº: {processo_numero}
- Vara/Juízo: {vara_juizo}, Comarca de {comarca}
- Autor: {autor_nome}
- Réu/Contestante: {cliente_nome}

## PETIÇÃO INICIAL DO AUTOR:
{peticao_inicial_completa}

## ANÁLISE ESTRATÉGICA (FIRAC):
{firac_analise}

## INSTRUÇÃO DE DEFESA DO ADVOGADO:
{argumentos_merito}

## PRELIMINARES A ARGUIR:
{preliminares_selecionadas}

## PROVAS DISPONÍVEIS:
Documentos: {documentos_anexos}
Provas a produzir: {provas_a_produzir}

## JURISPRUDÊNCIA FAVORÁVEL AO RÉU:
{jurisprudencia_favoravel}

## MODELOS DE REFERÊNCIA:
{modelos_contestacao_similares}

---

**TAREFA:**
Redija uma CONTESTAÇÃO COMPLETA e juridicamente fundamentada, seguindo a estrutura abaixo:

1. **Endereçamento Formal**
   - Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) de Direito da {vara_juizo}, Comarca de {comarca}

2. **Qualificação das Partes**
   - Contestante: {cliente_nome}, {cliente_qualificacao}
   - Autor: {autor_nome}
   - Advogado: {advogado_nome}, OAB {advogado_oab}

3. **PRELIMINARES** (se houver)
   - Desenvolva CADA preliminar selecionada com:
     * Fundamento legal (CPC)
     * Argumentação jurídica sólida
     * Citação de jurisprudência (usar {jurisprudencia_favoravel})
   
   PRELIMINARES A DESENVOLVER:
   {preliminares_selecionadas}

4. **DO MÉRITO**
   - Refute OS FATOS narrados na inicial ponto a ponto
   - Use {argumentos_merito} como direção estratégica
   - Contraste com provas disponíveis em {documentos_anexos}
   - Apresente a VERSÃO DO RÉU de forma convincente
   - Demonstre inconsistências na inicial
   - Cite jurisprudência contrária aos argumentos do autor

5. **IMPUGNAÇÃO AO VALOR DA CAUSA** (se aplicável)
   {impugnacao_valor_causa}

6. **DA LITIGÂNCIA DE MÁ-FÉ DO AUTOR** (se aplicável)
   {litigancia_ma_fe}

7. **DAS PROVAS**
   - Liste documentos anexos
   - Especifique provas a produzir: {provas_a_produzir}

8. **DOS PEDIDOS**
   {pedidos_principais}
   
   Sempre incluir:
   - Acolhimento das preliminares (se houver)
   - IMPROCEDÊNCIA TOTAL do pedido inicial
   - Condenação do autor em custas processuais e honorários advocatícios

9. **Data e Assinatura**
   Cidade, {data_hoje}
   {advogado_nome}
   OAB {advogado_oab}

---

**DIRETRIZES DE ESTILO:**
- Linguagem formal e técnica
- Argumentação lógica e persuasiva
- Citar artigos do CPC, CC e legislação específica
- Usar jurisprudência de tribunais superiores (STJ, STF) quando disponível
- Evitar adjetivações desnecessárias
- Foco na DEFESA do contestante (não apenas negar, mas PROVAR a versão do réu)
- Extensão: 8-15 páginas (depende da complexidade)

**ATENÇÃO:**
- NÃO criar fatos inexistentes
- NÃO citar jurisprudência inventada (usar apenas {jurisprudencia_favoravel})
- Basear-se ESTRITAMENTE em {argumentos_merito} e {documentos_anexos}
- Se informação não disponível, usar [INSERIR: descrição]

Redija agora a Contestação completa:
"""
)
```

### Endpoint Flask:

```python
@bp.route('/processos/<int:id_processo>/peticao/contestacao', methods=['GET', 'POST'])
@login_required
def ui_peticao_gerar_contestacao(id_processo):
    processo = get_processo_by_id(id_processo)
    
    if request.method == 'GET':
        # Buscar petição inicial do processo (se existir no BD)
        peticao_inicial = get_peticao_by_tipo(id_processo, 'inicial')
        
        # Buscar FIRAC
        firac_data = pipeline_firac(id_processo)
        
        # Listar partes adversas (réu é o cliente atual, autor é parte adversa)
        partes_adversas = get_partes_adversas(id_processo)
        
        return render_template('contestacao_form.html',
                             processo=processo,
                             peticao_inicial=peticao_inicial,
                             firac=firac_data,
                             partes_adversas=partes_adversas)
    
    if request.method == 'POST':
        # Coletar dados do formulário
        dados_ui = {
            'advogado': request.form.get('advogado'),
            'preliminares': request.form.getlist('preliminares'),
            'argumentos_merito': request.form.get('argumentos_merito'),
            'impugnacao_valor': request.form.get('impugnacao_valor') == 'on',
            'novo_valor': request.form.get('novo_valor'),
            'ma_fe': request.form.get('ma_fe') == 'on',
            'ma_fe_justificativa': request.form.get('ma_fe_justificativa'),
            'provas_produzir': request.form.getlist('provas_produzir'),
            'pedidos': request.form.get('pedidos')
        }
        
        # Buscar contexto via RAG
        peticao_inicial_completa = rag_buscar_peticao_inicial(id_processo)
        jurisprudencia = rag_buscar_jurisprudencia(
            query=f"defesa {processo.area_atuacao}",
            filtro_favoravel="reu"
        )
        modelos = rag_buscar_modelos_contestacao(processo.area_atuacao)
        
        # Gerar contestação
        contestacao_texto = generate_contestacao(
            dados_ui=dados_ui,
            processo=processo,
            peticao_inicial=peticao_inicial_completa,
            firac=firac_data,
            jurisprudencia=jurisprudencia,
            modelos=modelos
        )
        
        # Salvar no BD
        save_peticao(id_processo, 'contestacao', contestacao_texto)
        
        return render_template('contestacao_result.html',
                             contestacao=contestacao_texto,
                             processo=processo)
```

### Template HTML (`contestacao_form.html`):

```html
{% extends "base.html" %}

{% block content %}
<h2>Gerar Contestação - Processo {{ processo.numero_cnj }}</h2>

<form method="POST" enctype="multipart/form-data">
    <!-- Dados Básicos -->
    <div class="card mb-3">
        <div class="card-header">Dados Básicos</div>
        <div class="card-body">
            <div class="mb-3">
                <label>Advogado(a) Responsável</label>
                <select name="advogado" class="form-control" required>
                    {% for adv in advogados %}
                    <option value="{{ adv.id }}">{{ adv.nome }} - OAB {{ adv.oab }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="mb-3">
                <label>Cliente (Contestante/Réu)</label>
                <input type="text" class="form-control" 
                       value="{{ processo.cliente.nome_completo }}" readonly>
            </div>
            
            <div class="mb-3">
                <label>Autor (Parte Adversa)</label>
                <select name="autor" class="form-control">
                    {% for parte in partes_adversas %}
                    <option value="{{ parte.id }}">{{ parte.nome_completo }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
    </div>

    <!-- Preliminares -->
    <div class="card mb-3">
        <div class="card-header">Preliminares a Arguir</div>
        <div class="card-body">
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="ilegitimidade_passiva" class="form-check-input">
                <label class="form-check-label">Ilegitimidade Passiva</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="falta_interesse" class="form-check-input">
                <label class="form-check-label">Falta de Interesse de Agir</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="inepcia_inicial" class="form-check-input">
                <label class="form-check-label">Inépcia da Inicial</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="incompetencia" class="form-check-input">
                <label class="form-check-label">Incompetência do Juízo</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="prescricao" class="form-check-input">
                <label class="form-check-label">Prescrição/Decadência</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="preliminares" value="coisa_julgada" class="form-check-input">
                <label class="form-check-label">Coisa Julgada</label>
            </div>
        </div>
    </div>

    <!-- Mérito -->
    <div class="card mb-3">
        <div class="card-header">Argumentos de Mérito</div>
        <div class="card-body">
            <div class="mb-3">
                <label>Descreva a VERSÃO DO RÉU e os argumentos de defesa:</label>
                <textarea name="argumentos_merito" class="form-control" rows="10" required
                          placeholder="Ex: O réu nega categoricamente os fatos narrados na inicial. Na verdade, o contrato foi cumprido integralmente..."></textarea>
            </div>
        </div>
    </div>

    <!-- Valor da Causa -->
    <div class="card mb-3">
        <div class="card-header">Valor da Causa</div>
        <div class="card-body">
            <div class="form-check mb-2">
                <input type="checkbox" name="impugnacao_valor" class="form-check-input" id="impugnacao_valor">
                <label class="form-check-label" for="impugnacao_valor">Impugnar Valor da Causa</label>
            </div>
            <div id="novo_valor_div" style="display:none;">
                <label>Novo Valor Correto:</label>
                <input type="number" name="novo_valor" class="form-control" step="0.01">
            </div>
        </div>
    </div>

    <!-- Litigância de Má-Fé -->
    <div class="card mb-3">
        <div class="card-header">Litigância de Má-Fé</div>
        <div class="card-body">
            <div class="form-check mb-2">
                <input type="checkbox" name="ma_fe" class="form-check-input" id="ma_fe">
                <label class="form-check-label" for="ma_fe">Alegar Litigância de Má-Fé do Autor</label>
            </div>
            <div id="ma_fe_div" style="display:none;">
                <label>Justificativa:</label>
                <textarea name="ma_fe_justificativa" class="form-control" rows="3"></textarea>
            </div>
        </div>
    </div>

    <!-- Provas -->
    <div class="card mb-3">
        <div class="card-header">Provas</div>
        <div class="card-body">
            <div class="mb-3">
                <label>Documentos em Anexo:</label>
                <input type="file" name="documentos[]" class="form-control" multiple>
            </div>
            
            <label>Provas a Produzir:</label>
            <div class="form-check">
                <input type="checkbox" name="provas_produzir" value="testemunhal" class="form-check-input">
                <label class="form-check-label">Prova Testemunhal</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="provas_produzir" value="pericial" class="form-check-input">
                <label class="form-check-label">Prova Pericial</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="provas_produzir" value="depoimento_autor" class="form-check-input">
                <label class="form-check-label">Depoimento Pessoal do Autor</label>
            </div>
            <div class="form-check">
                <input type="checkbox" name="provas_produzir" value="inspecao" class="form-check-input">
                <label class="form-check-label">Inspeção Judicial</label>
            </div>
        </div>
    </div>

    <!-- Pedidos -->
    <div class="card mb-3">
        <div class="card-header">Pedidos</div>
        <div class="card-body">
            <textarea name="pedidos" class="form-control" rows="5"
                      placeholder="Ex: Condenação do autor ao pagamento de indenização por danos morais no valor de R$ 10.000,00...">- Acolhimento das preliminares arguidas;
- TOTAL IMPROCEDÊNCIA do pedido inicial;
- Condenação do autor em custas processuais e honorários advocatícios no percentual de 20% sobre o valor da causa.</textarea>
        </div>
    </div>

    <button type="submit" class="btn btn-primary btn-lg">
        <i class="fas fa-robot"></i> Gerar Contestação com IA
    </button>
</form>

<script>
document.getElementById('impugnacao_valor').addEventListener('change', function() {
    document.getElementById('novo_valor_div').style.display = this.checked ? 'block' : 'none';
});

document.getElementById('ma_fe').addEventListener('change', function() {
    document.getElementById('ma_fe_div').style.display = this.checked ? 'block' : 'none';
});
</script>
{% endblock %}
```

---

## 🔧 ESPECIFICAÇÃO TÉCNICA - RECLAMAÇÃO TRABALHISTA

### Prompt LangChain:

```python
RECLAMACAO_TRABALHISTA_PROMPT = PromptTemplate(
    input_variables=[
        "advogado_nome",
        "advogado_oab",
        "reclamante_nome",
        "reclamante_qualificacao",
        "reclamante_pis",
        "gratuidade_justica",
        "reclamada_nome",
        "reclamada_cnpj",
        "reclamada_endereco",
        "data_admissao",
        "data_demissao",
        "funcao_cargo",
        "ultimo_salario",
        "tipo_jornada",
        "tipo_rescisao",
        "verbas_reclamadas",  # Lista
        "horas_extras",  # Dict com média e percentual
        "danos_morais",  # Dict com descrição e valor
        "insalubridade_periculosidade",  # Dict
        "documentos_anexos",
        "testemunhas",  # Lista
        "vara_trabalho",
        "comarca",
        "ctps_dados",  # OCR extraction (opcional)
        "contracheques",  # Lista de valores
        "jurisprudencia_tst",  # RAG busca
        "modelos_reclamacao_similares"  # RAG busca
    ],
    template="""
Você é um advogado trabalhista brasileiro, especializado em reclamações trabalhistas e direitos do empregado.

## DADOS DO CASO:
- Vara: {vara_trabalho}, Comarca de {comarca}
- Reclamante: {reclamante_nome}
- Reclamada: {reclamada_nome} (CNPJ: {reclamada_cnpj})
- Admissão: {data_admissao}
- Demissão: {data_demissao}
- Função: {funcao_cargo}
- Último Salário: R$ {ultimo_salario}
- Jornada: {tipo_jornada}
- Tipo de Rescisão: {tipo_rescisao}

## VERBAS RECLAMADAS:
{verbas_reclamadas}

## DETALHES ESPECÍFICOS:
Horas Extras: {horas_extras}
Danos Morais: {danos_morais}
Insalubridade/Periculosidade: {insalubridade_periculosidade}

## DOCUMENTOS DISPONÍVEIS:
{documentos_anexos}

## TESTEMUNHAS:
{testemunhas}

## JURISPRUDÊNCIA TST:
{jurisprudencia_tst}

## MODELOS DE REFERÊNCIA:
{modelos_reclamacao_similares}

---

**TAREFA:**
Redija uma RECLAMAÇÃO TRABALHISTA COMPLETA, seguindo a estrutura da Justiça do Trabalho:

1. **Endereçamento**
   Excelentíssimo(a) Senhor(a) Doutor(a) Juiz(a) do Trabalho da {vara_trabalho}, Comarca de {comarca}

2. **RECLAMANTE**
   - Nome: {reclamante_nome}
   - {reclamante_qualificacao}
   - PIS: {reclamante_pis}
   {% if gratuidade_justica %}
   - Requer os benefícios da justiça gratuita (art. 790, §3º, CLT)
   {% endif %}

3. **RECLAMADA**
   - Razão Social: {reclamada_nome}
   - CNPJ: {reclamada_cnpj}
   - Endereço: {reclamada_endereco}

4. **SÍNTESE DOS FATOS**
   - Narrar admissão ({data_admissao})
   - Descrever função ({funcao_cargo}) e atividades
   - Detalhar jornada ({tipo_jornada})
   - Explicar salário (R$ {ultimo_salario})
   - Descrever demissão ({data_demissao}, tipo: {tipo_rescisao})
   - Expor irregularidades (verbas não pagas, condições de trabalho)

5. **DIREITOS LESADOS**
   Para CADA verba em {verbas_reclamadas}, desenvolver:
   - Fundamento legal (CLT, Súmulas TST)
   - Cálculo estimado (quando aplicável)
   - Jurisprudência de {jurisprudencia_tst}

   Verbas específicas:
   {% if 'horas_extras' in verbas_reclamadas %}
   - HORAS EXTRAS: {horas_extras.media_mensal}h/mês x {horas_extras.percentual}%
     * Reflexos em DSR, férias + 1/3, 13º salário, FGTS + 40%
     * Súmula 340 TST (cálculo)
   {% endif %}
   
   {% if 'danos_morais' in verbas_reclamadas %}
   - DANOS MORAIS: {danos_morais.descricao}
     * Valor estimado: R$ {danos_morais.valor}
     * Fundamento: CF/88 art. 5º, V e X; CLT art. 223-A a 223-G
     * Precedentes TST
   {% endif %}
   
   {% if 'insalubridade' in verbas_reclamadas %}
   - ADICIONAL DE INSALUBRIDADE: {insalubridade_periculosidade.tipo}
     * NR-15 (grau {insalubridade_periculosidade.grau})
     * Necessária perícia
   {% endif %}

6. **FUNDAMENTO LEGAL**
   - CLT (artigos pertinentes)
   - Súmulas TST
   - Orientações Jurisprudenciais (OJ)
   - CF/88

7. **DOS PEDIDOS**
   Listar TODOS os pedidos relacionados a {verbas_reclamadas}:
   - Reconhecimento de direitos
   - Pagamento de verbas
   - Indenizações
   - Multas (art. 467, 477, §8º CLT)
   - Juros e correção monetária
   - Honorários advocatícios (15%)

8. **VALOR DA CAUSA**
   Calcular soma estimada de todas verbas

9. **PROVAS**
   - Documental: {documentos_anexos}
   - Testemunhal: {testemunhas} (máximo 3)
   {% if insalubridade_periculosidade %}
   - Pericial: Insalubridade/Periculosidade
   {% endif %}

10. **REQUERIMENTOS FINAIS**
    - Citação da reclamada
    - Audiência de conciliação
    {% if 'aposentadoria' in verbas_reclamadas %}
    - Intimação do INSS
    {% endif %}
    - Condenação em honorários
    - Todos demais termos de direito

11. **Data e Assinatura**
    {comarca}, {data_hoje}
    {advogado_nome}
    OAB {advogado_oab}

---

**DIRETRIZES DE ESTILO:**
- Linguagem técnica trabalhista (CLT, TST)
- Estrutura clara e objetiva
- Citar Súmulas TST e OJ sempre que relevante
- Cálculos detalhados (quando possível estimar)
- Enfatizar direitos violados
- Tom profissional mas contundente
- Extensão: 10-20 páginas (depende das verbas)

**ATENÇÃO:**
- NÃO inventar fatos
- NÃO citar Súmulas inexistentes (usar apenas {jurisprudencia_tst})
- Cálculos aproximados (avisar que são estimativas)
- Se dados incompletos, usar [INSERIR: descrição]

Redija agora a Reclamação Trabalhista completa:
"""
)
```

### Endpoint Flask:

```python
@bp.route('/processos/<int:id_processo>/peticao/reclamacao-trabalhista', methods=['GET', 'POST'])
@login_required
def ui_peticao_gerar_reclamacao_trabalhista(id_processo):
    processo = get_processo_by_id(id_processo)
    
    if request.method == 'GET':
        return render_template('reclamacao_trabalhista_form.html',
                             processo=processo)
    
    if request.method == 'POST':
        # Coletar dados extensos do formulário
        dados_ui = {
            'advogado': request.form.get('advogado'),
            'reclamante_pis': request.form.get('pis'),
            'gratuidade': request.form.get('gratuidade') == 'on',
            'data_admissao': request.form.get('data_admissao'),
            'data_demissao': request.form.get('data_demissao'),
            'funcao': request.form.get('funcao'),
            'salario': request.form.get('salario'),
            'jornada': request.form.get('jornada'),
            'tipo_rescisao': request.form.get('tipo_rescisao'),
            'verbas': request.form.getlist('verbas'),
            'horas_extras': {
                'media': request.form.get('he_media'),
                'percentual': request.form.get('he_percentual')
            },
            'danos_morais': {
                'descricao': request.form.get('dm_descricao'),
                'valor': request.form.get('dm_valor')
            },
            'testemunhas': parse_testemunhas(request.form)
        }
        
        # Buscar contexto RAG
        jurisprudencia_tst = rag_buscar_jurisprudencia_tst(dados_ui['verbas'])
        modelos = rag_buscar_modelos_reclamacao_trabalhista()
        
        # Gerar reclamação
        reclamacao_texto = generate_reclamacao_trabalhista(
            dados_ui=dados_ui,
            processo=processo,
            jurisprudencia=jurisprudencia_tst,
            modelos=modelos
        )
        
        # Salvar no BD
        save_peticao(id_processo, 'reclamacao_trabalhista', reclamacao_texto)
        
        return render_template('reclamacao_trabalhista_result.html',
                             reclamacao=reclamacao_texto,
                             processo=processo)
```

---

## 📅 IMPLEMENTAÇÃO - ROADMAP

### Semana 5 (09-13/12) - Detalhado:

#### **Segunda-feira 09/12 - Contestação**
**Paulo + Dev #1 (8h):**
- [ ] Criar `CONTESTACAO_PROMPT` em `petition_module.py`
- [ ] Método `generate_contestacao()`
- [ ] Endpoint Flask `/processos/<id>/peticao/contestacao`
- [ ] Template `contestacao_form.html`
- [ ] Template `contestacao_result.html`
- [ ] Integração RAG (buscar petição inicial do processo)
- [ ] Testar com caso real
- [ ] Commit + Push

**Entregável:** Contestação funcional ✅

---

#### **Terça-feira 10/12 - Reclamação Trabalhista (Parte 1)**
**Paulo + Dev #1 (8h):**
- [ ] Criar `RECLAMACAO_TRABALHISTA_PROMPT`
- [ ] Método `generate_reclamacao_trabalhista()`
- [ ] Template `reclamacao_trabalhista_form.html` (extenso)
- [ ] Lógica de cálculo de verbas (helper functions)

**Entregável:** 50% Reclamação Trabalhista ⏳

---

#### **Quarta-feira 11/12 - Reclamação Trabalhista (Parte 2)**
**Paulo + Dev #1 (8h):**
- [ ] Endpoint Flask completo
- [ ] Template result
- [ ] Integração RAG (buscar Súmulas TST)
- [ ] Testar com caso real trabalhista
- [ ] Documentar campos do formulário
- [ ] Commit + Push

**Entregável:** Reclamação Trabalhista 100% funcional ✅

---

#### **Quinta-feira 12/12 - Testes & Refinamentos**
**Time Todo (8h):**
- [ ] Testar Contestação (5 casos diferentes)
- [ ] Testar Reclamação Trabalhista (5 casos)
- [ ] Validar jurisprudência citada (não inventada)
- [ ] Corrigir bugs
- [ ] Melhorar UX dos formulários
- [ ] Deploy em produção

**Entregável:** 2 tipos novos de petição testados ✅

---

#### **Sexta-feira 13/12 - Deploy & Documentação**
**Time Todo (4h):**
- [ ] Documentar novos tipos (manual do usuário)
- [ ] Gravar vídeos demo (Contestação + Reclamação)
- [ ] Atualizar FAQ
- [ ] Preparar para apresentação 15/12

**Entregável:** Sistema completo documentado ✅

---

## ✅ CHECKLIST FINAL

### Fase 1 (MVP - 28/11):
- [x] Petição Inicial (já implementada)
- [ ] 6 items reformatados (1,2,3,4,8,10)

### Fase 2 (até 15/12):
- [ ] Items 5, 6, 7 (RAG, Celery, Robot PJe)
- [ ] Contestação (Civil) - 09/12
- [ ] Reclamação Trabalhista - 10-11/12
- [ ] Testes completos - 12/12

### Apresentação 15/12:
- [ ] Demo completo (3 tipos de petições)
- [ ] Feedback de clientes
- [ ] V2.0 planejada

---

## 📚 REFERÊNCIAS

### Legislação:
- **CLT:** https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452.htm
- **CPC/2015:** https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm
- **Súmulas TST:** https://www.tst.jus.br/sumulas

### Modelos:
- PDFs analisados: `Peticoes Área Civil.pdf`, `Peticoes Trabalhistas.pdf`
- KB Global (quando implementada)

---

*Análise criada em 11/11/2025*  
*Última atualização: 11/11/2025*  
*Status: ✅ ANÁLISE COMPLETA - PRONTA PARA IMPLEMENTAÇÃO*
