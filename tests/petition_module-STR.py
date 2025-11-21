# petition_module.py
import logging
import json
import re
from typing import Dict, Any
from datetime import datetime # Movida para cá

from langchain_community.chat_models import ChatOpenAI 
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)

class PetitionGenerator:
    # Template da Petição como atributo de classe
    PETICAO_INICIAL_TEMPLATE = """
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA {juizo_vara} VARA {juizo_especialidade} DA COMARCA DE {juizo_comarca} - {juizo_uf}

Autos nº: (espaço para o número do processo, se houver distribuição prévia)

{autor_qualificacao_completa}, por seu advogado infra-assinado (procuração anexa - Doc. {procuracao_doc_numero}), com escritório profissional situado à {advogado_escritorio_endereco}, endereço eletrônico {advogado_email_contato}, onde recebe intimações e notificações, vem, mui respeitosamente, à presença de Vossa Excelência, com fulcro nos artigos {artigos_fundamentacao_chave}, propor a presente

{nome_completo_acao}

em face de {reu_qualificacao_completa}, pelos fatos e fundamentos jurídicos a seguir aduzidos:

I - DA GRATUIDADE DE JUSTIÇA (Opcional - Se Aplicável)
{secao_gratuidade_justica}

II - DOS FATOS
{narrativa_dos_fatos}

III - DO DIREITO
{fundamentacao_juridica_geral}

    III.1 - {titulo_fundamento_especifico_1}
    {texto_fundamento_especifico_1}

    III.2 - {titulo_fundamento_especifico_2}
    {texto_fundamento_especifico_2}

    (Podem haver mais subseções de direito conforme a complexidade)

    III.X - DA JURISPRUDÊNCIA APLICÁVEL (Opcional)
    {jurisprudencia_relevante}

IV - DA TUTELA DE URGÊNCIA (Opcional - Se Aplicável)
{secao_tutela_urgencia}

V - DOS PEDIDOS
Ante o exposto, requer a Vossa Excelência:
{lista_completa_dos_pedidos_formatada}

VI - DAS PROVAS
{texto_das_provas_especificas}

VII - DO VALOR DA CAUSA
Dá-se à causa o valor de R$ {valor_da_causa_numerico} ({valor_da_causa_por_extenso}).

Nesses Termos,
Pede Deferimento.

{cidade_peticao}, {data_peticao}.

_________________________________________
{nome_advogado_assinatura}
OAB/{uf_oab} nº {numero_oab}
""" # Fim do template

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._initialize_peticao_prompts_and_chains()

    def _initialize_peticao_prompts_and_chains(self):
        # (Código dos Prompts NOME_ACAO_PETICAO, ARTIGOS_CHAVE_PETICAO, NARRATIVA_FATOS_PETICAO,
        #  FUNDAMENTACAO_GERAL_PETICAO, LISTA_PEDIDOS_COMPLETA_PETICAO e suas respectivas LLMChains,
        #  como na versão anterior do pipeline.py _initialize_peticao_prompts_and_chains)
        self.NOME_ACAO_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_issue", "firac_conclusion"], template="Considerando a questão jurídica central: \"{firac_issue}\"\nE a conclusão alcançada: \"{firac_conclusion}\"\nSugira um nome formal, completo e tecnicamente adequado para a ação judicial a ser proposta em PORTUGUÊS. Inclua, se pertinente, cumulações de pedidos (ex: \"com pedido de tutela de urgência\", \"cumulada com danos morais\").\nRetorne apenas o nome da ação.\nNome Completo da Ação:")
        self.nome_acao_peticao_chain = LLMChain(llm=self.llm, prompt=self.NOME_ACAO_PETICAO_PROMPT, output_key="nome_completo_acao")
        self.ARTIGOS_CHAVE_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_rules"], template="Com base nas seguintes regras e normas identificadas para o caso:\n{firac_rules}\nListe, de forma concisa, os principais artigos de lei (ex: \"Art. 186 e 927 do Código Civil\", \"Art. 5º, X da Constituição Federal\") que devem ser mencionados como fundamento principal na introdução de uma petição inicial (\"com fulcro nos artigos...\"). Responda em PORTUGUÊS.\nArtigos de Fundamentação Chave:")
        self.artigos_chave_peticao_chain = LLMChain(llm=self.llm, prompt=self.ARTIGOS_CHAVE_PETICAO_PROMPT, output_key="artigos_fundamentacao_chave")
        self.NARRATIVA_FATOS_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_facts"], template="Os seguintes são os fatos relevantes de um caso jurídico, extraídos de uma análise FIRAC:\n{firac_facts}\nRe-escreva esses fatos como uma narrativa coesa, clara, em ordem cronológica (ou lógica mais apropriada), e detalhada o suficiente para a seção \"II - DOS FATOS\" de uma petição inicial. Use linguagem formal jurídica, seja objetivo e atenha-se aos fatos apresentados. A narrativa deve ser em PORTUGUÊS.\nNarrativa dos Fatos para Petição:")
        self.narrativa_fatos_peticao_chain = LLMChain(llm=self.llm, prompt=self.NARRATIVA_FATOS_PETICAO_PROMPT, output_key="narrativa_dos_fatos")
        self.FUNDAMENTACAO_GERAL_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_issue", "firac_rules", "firac_application"], template="Para uma petição inicial, redija a seção \"III - DO DIREITO\".\nA questão jurídica é: {firac_issue}\nAs regras aplicáveis são: {firac_rules}\nA aplicação dessas regras aos fatos resultou em: {firac_application}\nEstruture a fundamentação jurídica de forma lógica e persuasiva, citando as regras e explicando como elas se aplicam aos fatos para sustentar o direito do autor. Se houver múltiplos fundamentos, você PODE dividi-los em subseções com títulos apropriados (ex: III.1 Do Dano Material, III.2 Do Dano Moral). Responda em PORTUGUÊS.\nFundamentação Jurídica Completa (para a seção \"DO DIREITO\"):" )
        self.fundamentacao_geral_peticao_chain = LLMChain(llm=self.llm, prompt=self.FUNDAMENTACAO_GERAL_PETICAO_PROMPT, output_key="fundamentacao_juridica_geral")
        self.LISTA_PEDIDOS_COMPLETA_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_conclusion", "firac_issue"],template="""A conclusão de uma análise FIRAC para um caso relacionado à questão jurídica "{firac_issue}" é:\n{firac_conclusion}\nCom base nesta conclusão, formule TODOS os pedidos (principais e acessórios) que devem constar no item "V - DOS PEDIDOS" de uma petição inicial.\nFormate cada pedido em uma nova linha, começando com uma alínea (ex: "a) ...;", "b) ...;", etc.).\nInclua pedidos comuns como:\n1. A citação do Réu.\n2. O pedido principal decorrente da conclusão do caso (seja específico).\n3. Outros pedidos acessórios ou secundários relevantes para o caso.\n4. A condenação do Réu ao pagamento de custas processuais e honorários advocatícios.\n5. O protesto pela produção de todas as provas admitidas em direito.\nSe aplicável, inclua um pedido de gratuidade de justiça ou tutela de urgência no início da lista de pedidos, se a conclusão do caso sugerir. Responda em PORTUGUÊS.\n\nLISTA COMPLETA DE PEDIDOS FORMATADOS PARA PETIÇÃO (um por linha, com alíneas):""")
        self.lista_pedidos_completa_peticao_chain = LLMChain(llm=self.llm, prompt=self.LISTA_PEDIDOS_COMPLETA_PETICAO_PROMPT, output_key="lista_completa_dos_pedidos_formatada")


    def generate_peticao_rascunho(self, dados_ui: Dict[str, Any], firac_results: Dict[str, str]) -> str:
        # (Código mantido da versão anterior do pipeline.py, com a correção para pedidos_especificos_formatados
        #  e usando self.PETICAO_INICIAL_TEMPLATE e as chains definidas nesta classe)
        logger.info("Gerando rascunho de petição inicial (PetitionGenerator)...")
        template_data: Dict[str, Any] = {} 
        autor = dados_ui.get("autor", {})
        reu = dados_ui.get("reu", {})
        juizo = dados_ui.get("juizo", {})
        advogado = dados_ui.get("advogado", {})
        outros_dados = dados_ui.get("outros", {})

        # Populando template_data com campos individuais para qualificação
        template_data["juizo_vara"] = juizo.get("vara", "[VARA]")
        template_data["juizo_especialidade"] = juizo.get("especialidade", "CÍVEL")
        template_data["juizo_comarca"] = juizo.get("comarca", "[COMARCA]")
        template_data["juizo_uf"] = juizo.get("uf", "XX")
        
        autor_qual_parts = [autor.get("nome_completo_ou_razao_social")]
        if autor.get("nacionalidade"): autor_qual_parts.append(autor.get("nacionalidade"))
        if autor.get("estado_civil"): autor_qual_parts.append(autor.get("estado_civil"))
        if autor.get("profissao"): autor_qual_parts.append(autor.get("profissao"))
        if autor.get("rg"): autor_qual_parts.append(f"portador(a) do RG nº {autor.get('rg')}")
        if autor.get("cpf"): autor_qual_parts.append(f"inscrito(a) no CPF/MF sob o nº {autor.get('cpf')}")
        if autor.get("endereco"): autor_qual_parts.append(f"residente e domiciliado(a) à {autor.get('endereco')}")
        if autor.get("email"): autor_qual_parts.append(f"com endereço eletrônico {autor.get('email')}")
        template_data["autor_qualificacao_completa"] = ", ".join(filter(None, autor_qual_parts))
        
        template_data["procuracao_doc_numero"] = outros_dados.get("procuracao_doc_num", "01")
        template_data["advogado_escritorio_endereco"] = advogado.get("escritorio_endereco", "[Endereço do Escritório]")
        template_data["advogado_email_contato"] = advogado.get("email", "[email.advogado@example.com]")
        
        reu_qual_list = [reu.get("nome", "[NOME DO RÉU]")]
        if reu.get("nacionalidade"): reu_qual_list.append(reu.get("nacionalidade"))
        if reu.get("estado_civil"): reu_qual_list.append(reu.get("estado_civil"))
        if reu.get("profissao"): reu_qual_list.append(reu.get("profissao"))
        if reu.get("rg"): reu_qual_list.append(f"portador(a) do RG nº {reu.get('rg')}")
        if reu.get("cpf_cnpj"): reu_qual_list.append(f"inscrito(a) no CPF/CNPJ sob o nº {reu.get('cpf_cnpj')}")
        if reu.get("endereco"): reu_qual_list.append(f"residente e domiciliado(a) em {reu.get('endereco')}")
        else: reu_qual_list.append("em local incerto e não sabido")
        if reu.get("email"): reu_qual_list.append(f"com endereço eletrônico {reu.get('email')}")
        template_data["reu_qualificacao_completa"] = ", ".join(filter(None, reu_qual_list))
        
        try:
            nome_acao_input = {"firac_issue": firac_results.get("issue", ""), "firac_conclusion": firac_results.get("conclusion", "")}
            nome_acao_output = self.nome_acao_peticao_chain.invoke(nome_acao_input)
            template_data["nome_completo_acao"] = nome_acao_output.get("nome_completo_acao", "AÇÃO JUDICIAL").strip().upper()

            artigos_input = {"firac_rules": firac_results.get("rules", "")}
            artigos_output = self.artigos_chave_peticao_chain.invoke(artigos_input)
            template_data["artigos_fundamentacao_chave"] = artigos_output.get("artigos_fundamentacao_chave", "").strip()
            
            fatos_input = {"firac_facts": firac_results.get("facts", "")}
            fatos_output = self.narrativa_fatos_peticao_chain.invoke(fatos_input)
            template_data["narrativa_dos_fatos"] = fatos_output.get("narrativa_dos_fatos", "[Narrar os fatos detalhadamente]")

            fund_input = {"firac_issue": firac_results.get("issue", ""), "firac_rules": firac_results.get("rules", ""), "firac_application": firac_results.get("application", "")}
            fund_output = self.fundamentacao_geral_peticao_chain.invoke(fund_input)
            template_data["fundamentacao_juridica_geral"] = fund_output.get("fundamentacao_juridica_geral", "[Fundamentação jurídica detalhada]")
            
            # Simplificando placeholders de subseções de direito (LLM deve incluí-los em fundamentacao_juridica_geral se instruído)
            template_data["titulo_fundamento_especifico_1"] = "" # Pode ser parte da saída de fundamentacao_juridica_geral
            template_data["texto_fundamento_especifico_1"] = ""  # Ou removidos do template se a geral já for completa
            template_data["titulo_fundamento_especifico_2"] = "" 
            template_data["texto_fundamento_especifico_2"] = ""  
            template_data["jurisprudencia_relevante"] = "" 

            # Pedidos: Usando o novo prompt para lista completa
            pedidos_input = {"firac_conclusion": firac_results.get("conclusion", ""), "firac_issue": firac_results.get("issue", "")}
            pedidos_output = self.lista_pedidos_completa_peticao_chain.invoke(pedidos_input)
            template_data["lista_completa_dos_pedidos_formatada"] = pedidos_output.get("lista_completa_dos_pedidos_formatada", "    a) [DEFINIR PEDIDOS];")
            
            template_data["secao_gratuidade_justica"] = outros_dados.get("texto_gratuidade", "(Seção de gratuidade de justiça a ser preenchida se aplicável, ou removida se não for o caso)")
            template_data["secao_tutela_urgencia"] = outros_dados.get("texto_tutela", "(Seção de tutela de urgência a ser preenchida se aplicável, ou removida se não for o caso)")
            default_provas = "Protesta provar o alegado por todos os meios de prova em direito admitidos, especialmente documental, testemunhal, pericial e depoimento pessoal do(a) Ré(u)."
            template_data["texto_das_provas_especificas"] = outros_dados.get("texto_provas_especificas") if outros_dados.get("texto_provas_especificas","").strip() else default_provas
            
            template_data["valor_da_causa_numerico"] = outros_dados.get("valor_causa_num", "[VALOR NUMÉRICO]")
            template_data["valor_da_causa_por_extenso"] = outros_dados.get("valor_causa_ext", "[valor por extenso]")
            template_data["cidade_peticao"] = advogado.get("cidade_peticao", "[Cidade]")
            
            template_data["data_peticao"] = datetime.now().strftime("%d de %B de %Y") # datetime importado no topo do módulo
            template_data["nome_advogado_assinatura"] = advogado.get("nome", "[Nome Advogado]")
            template_data["uf_oab"] = advogado.get("oab_uf", "XX")
            template_data["numero_oab"] = advogado.get("oab_numero", "[Num OAB]")

            logger.debug(f"Chaves em template_data para petição: {list(template_data.keys())}")
            peticao_final = self.PETICAO_INICIAL_TEMPLATE.format(**template_data)
            logger.info("Rascunho da petição inicial gerado com sucesso.")
            return peticao_final
        except KeyError as e_key: 
            logger.error(f"Erro de Chave ao formatar template da petição: Chave '{e_key}' ausente em template_data.")
            logger.debug(f"Chaves disponíveis em template_data: {list(template_data.keys())}")
            missing_in_template = [pk for pk in re.findall(r"\{(\w+)\}", self.PETICAO_INICIAL_TEMPLATE) if pk not in template_data]
            logger.error(f"Placeholders no template que não foram encontrados em template_data: {missing_in_template}")
            return f"ERRO INTERNO AO GERAR PETIÇÃO: Chave de formatação ausente '{e_key}'. Placeholders não preenchidos: {missing_in_template}."
        except Exception as e_geral:
            logger.error(f"Erro geral ao gerar rascunho da petição: {e_geral}", exc_info=True)
            return f"ERRO AO GERAR PETIÇÃO: {e_geral}"

