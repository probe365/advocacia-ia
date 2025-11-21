# petition_module.py
from email import utils
import logging
import json
import re
from typing import Dict, Any
from datetime import datetime # Movida para cá

from langchain_community.chat_models import ChatOpenAI 
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from utils.text_helpers import extract_text, format_date_pt, clean_text, normalize_name, format_cpf, format_cnpj, validate_cpf, validate_cnpj, detect_document_type

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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



    DEFAULT_DATA_PETICAO = format_date_pt()  # Data padrão formatada em português

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._initialize_peticao_prompts_and_chains()

    def _initialize_peticao_prompts_and_chains(self):
        # (Código dos Prompts NOME_ACAO_PETICAO, ARTIGOS_CHAVE_PETICAO, NARRATIVA_FATOS_PETICAO,
        #  FUNDAMENTACAO_GERAL_PETICAO, LISTA_PEDIDOS_COMPLETA_PETICAO e suas respectivas LLMChains,
        #  como na versão anterior do pipeline.py _initialize_peticao_prompts_and_chains)
        self.NOME_ACAO_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_issue", "firac_conclusion"], template="Questão jurídica: \"{firac_issue}\"\nConclusão: \"{firac_conclusion}\"\n\nGere APENAS o nome formal da ação judicial em PORTUGUÊS, sem explicações ou introduções.\nExemplos:\n- \"AÇÃO DE INDENIZAÇÃO POR DANOS MORAIS E MATERIAIS\"\n- \"AÇÃO DECLARATÓRIA DE NULIDADE DE CONTRATO CUMULADA COM REPETIÇÃO DE INDÉBITO\"\n\nResposta (SOMENTE o nome da ação):")
        self.nome_acao_peticao_chain = LLMChain(llm=self.llm, prompt=self.NOME_ACAO_PETICAO_PROMPT, output_key="nome_completo_acao")

        self.ARTIGOS_CHAVE_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_rules"], template="Com base nas seguintes regras e normas identificadas para o caso:\n{firac_rules}\n\nListe APENAS os artigos de lei, de forma CONCISA e DIRETA, sem explicações ou introduções. Use o formato: \"Art. X do [Lei], Art. Y do [Lei]\".\nExemplos corretos:\n- \"Art. 186 e 927 do Código Civil\"\n- \"Art. 5º, X da Constituição Federal e Art. 14 do CDC\"\n\nNÃO inclua:\n- Frases introdutórias\n- Explicações sobre o que os artigos dizem\n- Numeração ou marcadores\n\nResposta (SOMENTE os artigos):")
        self.artigos_chave_peticao_chain = LLMChain(llm=self.llm, prompt=self.ARTIGOS_CHAVE_PETICAO_PROMPT, output_key="artigos_fundamentacao_chave")
        
        self.NARRATIVA_FATOS_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_facts"], template="Os seguintes são os fatos relevantes de um caso jurídico, extraídos de uma análise FIRAC:\n{firac_facts}\nRe-escreva esses fatos como uma narrativa coesa, clara, em ordem cronológica (ou lógica mais apropriada), e detalhada o suficiente para a seção \"II - DOS FATOS\" de uma petição inicial. Use linguagem formal jurídica, seja objetivo e atenha-se aos fatos apresentados. A narrativa deve ser em PORTUGUÊS.\nNarrativa dos Fatos para Petição:")
        self.narrativa_fatos_peticao_chain = LLMChain(llm=self.llm, prompt=self.NARRATIVA_FATOS_PETICAO_PROMPT, output_key="narrativa_dos_fatos")
        
        self.FUNDAMENTACAO_GERAL_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_issue", "firac_rules", "firac_application"], template="Para uma petição inicial, redija a seção \"III - DO DIREITO\".\nA questão jurídica é: {firac_issue}\nAs regras aplicáveis são: {firac_rules}\nA aplicação dessas regras aos fatos resultou em: {firac_application}\nEstruture a fundamentação jurídica de forma lógica e persuasiva, citando as regras e explicando como elas se aplicam aos fatos para sustentar o direito do autor. Se houver múltiplos fundamentos, você PODE dividi-los em subseções com títulos apropriados (ex: III.1 Do Dano Material, III.2 Do Dano Moral). Responda em PORTUGUÊS.\nFundamentação Jurídica Completa (para a seção \"DO DIREITO\"):" )
        self.fundamentacao_geral_peticao_chain = LLMChain(llm=self.llm, prompt=self.FUNDAMENTACAO_GERAL_PETICAO_PROMPT, output_key="fundamentacao_juridica_geral")
        
        self.LISTA_PEDIDOS_COMPLETA_PETICAO_PROMPT = PromptTemplate(input_variables=["firac_conclusion", "firac_issue"],template="""A conclusão de uma análise FIRAC para um caso relacionado à questão jurídica "{firac_issue}" é:\n{firac_conclusion}\nCom base nesta conclusão, formule TODOS os pedidos (principais e acessórios) que devem constar no item "V - DOS PEDIDOS" de uma petição inicial.\nFormate cada pedido em uma nova linha, começando com uma alínea (ex: "a) ...;", "b) ...;", etc.).\nInclua pedidos comuns como:\n1. A citação do Réu.\n2. O pedido principal decorrente da conclusão do caso (seja específico).\n3. Outros pedidos acessórios ou secundários relevantes para o caso.\n4. A condenação do Réu ao pagamento de custas processuais e honorários advocatícios.\n5. O protesto pela produção de todas as provas admitidas em direito.\nSe aplicável, inclua um pedido de gratuidade de justiça ou tutela de urgência no início da lista de pedidos, se a conclusão do caso sugerir. Responda em PORTUGUÊS.\n\nLISTA COMPLETA DE PEDIDOS FORMATADOS PARA PETIÇÃO (um por linha, com alíneas):""")
        self.lista_pedidos_completa_peticao_chain = LLMChain(llm=self.llm, prompt=self.LISTA_PEDIDOS_COMPLETA_PETICAO_PROMPT, output_key="lista_completa_dos_pedidos_formatada")


    def _clean_llm_response(self, text: str, response_type: str = "general") -> str:
        """
        Limpa respostas do LLM removendo textos explicativos indesejados.
        
        Args:
            text: Texto a ser limpo
            response_type: Tipo de resposta ('artigos', 'nome_acao', 'general')
        """
        if not text:
            return text
            
        # Remove common introductory phrases
        unwanted_phrases = [
            r"^Para fundamentar.*?são:\s*",
            r"^Com base.*?seguir:\s*",
            r"^Os principais artigos.*?são:\s*",
            r"^Certamente[,!.]?\s*",
            r"^Claro[,!.]?\s*",
            r"^Aqui está.*?:\s*",
            r"^Segue.*?:\s*",
            r"^\d+\.\s*\*\*",  # Remove numbered lists like "1. **"
            r"\*\*$",  # Remove trailing **
        ]
        
        import re
        cleaned = text.strip()
        
        for pattern in unwanted_phrases:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # For artigos specifically, extract only the legal citations
        if response_type == "artigos":
            # Remove markdown bold markers
            cleaned = re.sub(r'\*\*', '', cleaned)
            # Remove explanatory text after dashes
            cleaned = re.sub(r'\s*-\s*[^,;\n]+(?=[,;\n]|$)', '', cleaned)
            # Remove numbered lists
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned, flags=re.MULTILINE)
            # Keep only the first sentence/line if multiple exist
            lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
            if lines:
                # Join articles that are on separate lines
                articles = []
                for line in lines:
                    if re.match(r'Art\.?\s+\d+', line, re.IGNORECASE):
                        articles.append(line)
                if articles:
                    cleaned = ', '.join(articles[:5])  # Max 5 articles
                else:
                    cleaned = lines[0]
        
        return cleaned.strip()

    def _validar_inputs_para_chain(self, chain: LLMChain, input_data: Dict[str, Any], chain_nome: str) -> bool:
        """
        Valida se todos os input_variables esperados pela chain estão presentes e não vazios.

        Args:
            chain (LLMChain): A chain que será validada.
            input_data (Dict[str, Any]): O dicionário de inputs que será passado para a chain.
            chain_nome (str): Nome da chain para fins de log.

        Returns:
            bool: True se todos os inputs estão válidos, False se houver faltantes ou vazios.
        """
        esperados = chain.prompt.input_variables
        faltantes = [var for var in esperados if var not in input_data]
        vazios = [var for var in esperados if not input_data.get(var)]

        if faltantes:
            logger.error(f"[VALIDADOR] Chain '{chain_nome}' está com variáveis faltantes: {faltantes}")
        if vazios:
            logger.warning(f"[VALIDADOR] Chain '{chain_nome}' está com variáveis vazias: {vazios}")

        return not faltantes and not vazios


    def generate_peticao_rascunho(self, dados_ui: Dict[str, Any], firac_results: Dict[str, str]) -> str:
        logger.debug(f"[TESTE] FIRAC Results:\n{json.dumps(firac_results, ensure_ascii=False, indent=2)}")
        logger.info("Gerando rascunho de petição inicial (PetitionGenerator)...")
        
        # DEBUG: Check what we received
        logger.info(f"[PETITION MODULE DEBUG] Received firac_results keys: {list(firac_results.keys())}")
        logger.info(f"[PETITION MODULE DEBUG] facts type: {type(firac_results.get('facts'))}, value: {firac_results.get('facts')}")
        logger.info(f"[PETITION MODULE DEBUG] rules type: {type(firac_results.get('rules'))}, value: {firac_results.get('rules')}")
        
        template_data: Dict[str, Any] = {}


        autor = dados_ui.get("autor", {})
        reu = dados_ui.get("reu", {})
        juizo = dados_ui.get("juizo", {})
        advogado = dados_ui.get("advogado", {})
        outros_dados = dados_ui.get("outros", {})

        # Juízo
        template_data["juizo_vara"] = juizo.get("vara", "[VARA]")
        template_data["juizo_especialidade"] = juizo.get("especialidade", "CÍVEL")
        template_data["juizo_comarca"] = juizo.get("comarca", "[COMARCA]")
        template_data["juizo_uf"] = juizo.get("uf", "SP")

        # Autor
        autor_qual_parts = [self._normalize_nome(autor.get("nome_completo_ou_razao_social", "[NOME AUTOR]"))]
        if autor.get("nacionalidade"): autor_qual_parts.append(autor.get("nacionalidade"))
        if autor.get("estado_civil"): autor_qual_parts.append(autor.get("estado_civil"))
        if autor.get("profissao"): autor_qual_parts.append(autor.get("profissao"))
        if autor.get("rg"): autor_qual_parts.append(f"portador(a) do RG nº {autor.get('rg')}")
        if autor.get("cpf"): autor_qual_parts.append(f"inscrito(a) no CPF/MF sob o nº {self._format_documento(autor.get('cpf'))}")
        if autor.get("endereco"): autor_qual_parts.append(f"residente e domiciliado(a) à {autor.get('endereco')}")
        if autor.get("email"): autor_qual_parts.append(f"com endereço eletrônico {autor.get('email')}")
        template_data["autor_qualificacao_completa"] = ", ".join(filter(None, autor_qual_parts))

        # Advogado
        template_data["procuracao_doc_numero"] = outros_dados.get("procuracao_doc_num", "01")
        template_data["advogado_escritorio_endereco"] = advogado.get("escritorio_endereco", "[Endereço do Escritório]")
        template_data["advogado_email_contato"] = advogado.get("email", "[email.advogado@example.com]")

        # Réu
        reu_qual_list = [self._normalize_nome(reu.get("nome", "[NOME DO RÉU]"))]
        if reu.get("nacionalidade"): reu_qual_list.append(reu.get("nacionalidade"))
        if reu.get("estado_civil"): reu_qual_list.append(reu.get("estado_civil"))
        if reu.get("profissao"): reu_qual_list.append(reu.get("profissao"))
        if reu.get("rg"): reu_qual_list.append(f"portador(a) do RG nº {reu.get('rg')}")
        if reu.get("cpf_cnpj"): reu_qual_list.append(f"inscrito(a) no CPF/CNPJ sob o nº {self._format_documento(reu.get('cpf_cnpj'))}")
        if reu.get("endereco"):
            reu_qual_list.append(f"residente e domiciliado(a) em {reu.get('endereco')}")
        else:
            reu_qual_list.append("em local incerto e não sabido")
        if reu.get("email"): reu_qual_list.append(f"com endereço eletrônico {reu.get('email')}")
        template_data["reu_qualificacao_completa"] = ", ".join(filter(None, reu_qual_list))

        try:
            # FIRAC seguro
            firac_data = {
                "facts": firac_results.get("facts", "[DADO NÃO DISPONÍVEL]"),
                "issue": firac_results.get("issue", "[DADO NÃO DISPONÍVEL]"),
                "rules": firac_results.get("rules", "[DADO NÃO DISPONÍVEL]"),
                "application": firac_results.get("application", "[DADO NÃO DISPONÍVEL]"),
                "conclusion": firac_results.get("conclusion", "[DADO NÃO DISPONÍVEL]")
            }

            # Nome da ação
            nome_acao_input = {"firac_issue": firac_data["issue"], "firac_conclusion": firac_data["conclusion"]}
            if self._validar_inputs_para_chain(self.nome_acao_peticao_chain, nome_acao_input, "nome_acao_peticao_chain"):
                nome_acao_output = self.nome_acao_peticao_chain.invoke(nome_acao_input)
                # Extract using the output_key from the chain
                nome_acao_text = nome_acao_output.get("nome_completo_acao", "")
                nome_acao_cleaned = self._clean_llm_response(nome_acao_text, "nome_acao")
                template_data["nome_completo_acao"] = clean_text(nome_acao_cleaned).upper()
            else:
                template_data["nome_completo_acao"] = "[Nome da ação não gerado]"


            # Artigos chave
            artigos_input = {"firac_rules": firac_results.get("rules", "")}
            if self._validar_inputs_para_chain(self.artigos_chave_peticao_chain, artigos_input, "artigos_chave_peticao_chain"):
                artigos_output = self.artigos_chave_peticao_chain.invoke(artigos_input)
                # Extract using the output_key from the chain
                artigos_text = artigos_output.get("artigos_fundamentacao_chave", "")
                artigos_cleaned = self._clean_llm_response(artigos_text, "artigos")
                template_data["artigos_fundamentacao_chave"] = clean_text(artigos_cleaned)
            else:
                template_data["artigos_fundamentacao_chave"] = "[Artigos chave não gerados]"


            fatos_input = {"firac_facts": firac_results.get("facts", "")}
            fatos_output = self.narrativa_fatos_peticao_chain.invoke(fatos_input)
            template_data["narrativa_dos_fatos"] = fatos_output.get("narrativa_dos_fatos", "[Narrar os fatos detalhadamente]")


            # Fundamentação jurídica geral
            fund_input = {"firac_issue": firac_results.get("issue", ""), "firac_rules": firac_results.get("rules", ""), "firac_application": firac_results.get("application", "")}
            if self._validar_inputs_para_chain(self.fundamentacao_geral_peticao_chain, fund_input, "fundamentacao_geral_peticao_chain"):
                fund_output = self.fundamentacao_geral_peticao_chain.invoke(fund_input)
                template_data["fundamentacao_juridica_geral"] = fund_output.get("fundamentacao_juridica_geral", "[Fundamentação jurídica detalhada]")
            else:
                template_data["fundamentacao_juridica_geral"] = "[Fundamentação jurídica detalhada]"

            # Pedidos: Usando o novo prompt para lista completa
            pedidos_input = {"firac_conclusion": firac_results.get("conclusion", ""), "firac_issue": firac_results.get("issue", "")}
            pedidos_output = self.lista_pedidos_completa_peticao_chain.invoke(pedidos_input)
            template_data["lista_completa_dos_pedidos_formatada"] = pedidos_output.get("lista_completa_dos_pedidos_formatada", "    a) [DEFINIR PEDIDOS];")
            
            # Seções adicionais
            template_data["secao_gratuidade_justica"] = clean_text(outros_dados.get("texto_gratuidade", "(Seção de gratuidade de justiça...)"))
            template_data["secao_tutela_urgencia"] = clean_text(outros_dados.get("texto_tutela", "(Seção de tutela de urgência...)"))

            default_provas = "Protesta provar o alegado por todos os meios de prova em direito admitidos..."
            template_data["texto_das_provas_especificas"] = clean_text(outros_dados.get("texto_provas_especificas", default_provas))

            # Valor da causa
            template_data["valor_da_causa_numerico"] = outros_dados.get("valor_causa_num", "[VALOR NUMÉRICO]")
            template_data["valor_da_causa_por_extenso"] = outros_dados.get("valor_causa_ext", "[valor por extenso]")

            # Local e data
            template_data["cidade_peticao"] = advogado.get("cidade_peticao", "[Cidade]")
            template_data["data_peticao"] = self._format_data()

            # Assinatura
            template_data["nome_advogado_assinatura"] = self._normalize_nome(advogado.get("nome", "[Nome Advogado]"))
            template_data["uf_oab"] = advogado.get("oab_uf", "XX")
            template_data["numero_oab"] = advogado.get("oab_numero", "[Num OAB]")

            # Preenche todos os placeholders do template com fallback seguro
            placeholders = re.findall(r"\{(\w+)\}", self.PETICAO_INICIAL_TEMPLATE)
            for p in placeholders:
                if p not in template_data:
                    template_data[p] = f"[{p} não preenchido]"

            for k, v in template_data.items():
                if not v:
                    logger.warning(f"Campo '{k}' está vazio ou nulo.")

            logger.debug(f"Chaves em template_data para petição: {list(template_data.keys())}")
            peticao_final = self.PETICAO_INICIAL_TEMPLATE.format(**template_data)
            logger.info("Rascunho da petição inicial gerado com sucesso.")
            logger.debug(f"Petição final:\n{peticao_final}")

            return peticao_final

        except KeyError as e_key:
            logger.error(f"Erro de Chave ao formatar template da petição: Chave '{e_key}' ausente em template_data.")
            missing_in_template = [pk for pk in re.findall(r"\{(\w+)\}", self.PETICAO_INICIAL_TEMPLATE) if pk not in template_data]
            return f"ERRO INTERNO AO GERAR PETIÇÃO: Chave de formatação ausente '{e_key}'. Placeholders não preenchidos: {missing_in_template}."
        except Exception as e_geral:
            logger.error(f"Erro geral ao gerar rascunho da petição: {e_geral}", exc_info=True)
            return f"ERRO AO GERAR PETIÇÃO: {e_geral}"
    
    def _format_documento(self, doc: str) -> str:
        """Formata CPF ou CNPJ com pontuação adequada."""
        doc = re.sub(r"\D", "", doc)
        if len(doc) == 11:
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        elif len(doc) == 14:
            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
        return doc  # Retorna como está se não for CPF/CNPJ válido

    def _normalize_nome(self, nome: str) -> str:
        """Normaliza nome próprio ou razão social."""
        return nome.strip().title() if nome else "[NOME]"

    def _format_data(self, data: str = None) -> str:
        """Formata a data atual ou uma data fornecida no padrão brasileiro."""
        from datetime import datetime
        if data:
            try:
                dt = datetime.strptime(data, "%Y-%m-%d")
            except ValueError:
                return data  # Se não conseguir converter, retorna como está
        else:
            dt = datetime.now()
        return dt.strftime("%d de %B de %Y")
    