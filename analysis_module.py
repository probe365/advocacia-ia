# analysis_module.py
import logging
import json
import re  # Para _clean_llm_json_output
from typing import Any, Dict, List, Protocol

from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain  # Para o chat_qa_chain
from langchain.chains.summarize import load_summarize_chain  # Para o summarize_chain

logger = logging.getLogger(__name__)


class RetrieverProtocol(Protocol):
    def get_relevant_documents(self, query: str) -> List[Any]:
        ...

class CaseAnalyzer:
    def __init__(self, llm: ChatOpenAI, 
                 case_retriever: RetrieverProtocol,
                 kb_retriever: RetrieverProtocol,
                 map_prompt_pt: PromptTemplate, # Passando os prompts de resumo
                 combine_prompt_pt: PromptTemplate):
        self.llm = llm
        self.case_retriever = case_retriever
        self.kb_retriever = kb_retriever
     
        # CaseAnalyzer cria sua própria chat_qa_chain
        self.chat_qa_chain = load_qa_chain(self.llm, chain_type="stuff")

        self.summarize_chain = load_summarize_chain(
            llm=self.llm, chain_type="map_reduce",
            map_prompt=map_prompt_pt, combine_prompt=combine_prompt_pt,
            verbose=True
        )

        # Inicializa prompts e chains de análise e FIRAC
        self._initialize_analysis_prompts_and_chains()
        self._initialize_firac_prompts_and_chains()

    def _initialize_analysis_prompts_and_chains(self):
        # (Código dos Prompts RISK, NEXT_STEPS
        #  e suas respectivas LLMChains, como na versão anterior do pipeline.py __init__)
        self.RISK_PROMPT = PromptTemplate(input_variables=["context", "client", "opponent"], template="Você é um advogado analisando um caso para o cliente {client} contra a parte oponente {opponent}...\nContexto dos Documentos do Caso:\n{context}\n\nFormato da resposta (use markdown):...") # Template completo omitido por brevidade
        self.risk_chain = LLMChain(llm=self.llm, prompt=self.RISK_PROMPT)
        self.NEXT_STEPS_PROMPT = PromptTemplate(input_variables=["context"], template="Você é um advogado consultor...\nContexto dos Documentos do Caso:\n{context}\n\nFormato da Resposta (use markdown):...")
        self.next_steps_chain = LLMChain(llm=self.llm, prompt=self.NEXT_STEPS_PROMPT)
        
    def _initialize_firac_prompts_and_chains(self):
        # (Código dos Prompts FACTS, ISSUE, RULE, APPLICATION, CONCLUSION
        #  e suas respectivas LLMChains, e o firac_chain (SequentialChain),
        #  como na versão anterior do pipeline.py __init__)
        self.FACTS_PROMPT = PromptTemplate(input_variables=["context"], template="Você é um assistente jurídico...\nContexto do Caso:\n{context}\n\nFATOS JURIDICAMENTE RELEVANTES:")
        self.ISSUE_PROMPT = PromptTemplate(input_variables=["facts"], template="Considerando os seguintes fatos...\n{facts}\n\nQUESTÃO(ÕES) JURÍDICA(S) CENTRAL(AIS):")
        self.RULE_PROMPT = PromptTemplate(input_variables=["issue", "context"], template="Para a(s) seguinte(s) questão(ões)...\n{issue}\n\nE contexto:\n{context}\n\nREGRAS (NORMAS E JURISPRUDÊNCIA) APLICÁVEIS:")
        self.APPLICATION_PROMPT = PromptTemplate(input_variables=["facts", "rules", "issue"], template="Analise a aplicação...\nQuestão: {issue}\n\nFatos:\n{facts}\n\nRegras:\n{rules}\n\nAPLICAÇÃO DAS REGRAS AOS FATOS:")
        self.CONCLUSION_PROMPT = PromptTemplate(input_variables=["application", "issue"], template="Com base na análise para a questão \"{issue}\":\n{application}\n\nCONCLUSÃO E ESTRATÉGIA INICIAL:")
        self.facts_chain = LLMChain(llm=self.llm, prompt=self.FACTS_PROMPT, output_key="facts")
        self.issue_chain = LLMChain(llm=self.llm, prompt=self.ISSUE_PROMPT, output_key="issue")
        self.rule_chain = LLMChain(llm=self.llm, prompt=self.RULE_PROMPT, output_key="rules")
        self.application_chain = LLMChain(llm=self.llm, prompt=self.APPLICATION_PROMPT, output_key="application")
        self.conclusion_chain = LLMChain(llm=self.llm, prompt=self.CONCLUSION_PROMPT, output_key="conclusion")
        self.firac_chain = SequentialChain(chains=[self.facts_chain, self.issue_chain, self.rule_chain, self.application_chain, self.conclusion_chain], input_variables=["context"], output_variables=["facts", "issue", "rules", "application", "conclusion"], verbose=True)

    # Métodos que foram movidos do Pipeline e agora usam self.llm, self.case_retriever etc.
    # Em analysis_module.py, dentro da classe CaseAnalyzer

    def chat(self, question: str, search_scope: str = "case_and_kb") -> Dict[str, Any]:
        """
        Responde a uma pergunta usando um escopo de busca definido:
        - "case_and_kb": Busca nos documentos do caso e na Base de Conhecimento.
        - "case_only": Busca apenas nos documentos do caso.
        - "kb_only": Busca apenas na Base de Conhecimento.
        """
        logger.info(f"Chat iniciado com a pergunta: '{question[:50]}...' no escopo: '{search_scope}'")
        
        all_relevant_docs = []
        
        # Coleta documentos com base no escopo selecionado
        if search_scope in ["case_and_kb", "case_only"]:
            logger.debug("Buscando em 'case_store'...")
            docs_case = self.case_retriever.get_relevant_documents(question)
            all_relevant_docs.extend(docs_case)
            logger.info(f"Encontrados {len(docs_case)} documento(s) relevantes no caso.")
            
        if search_scope in ["case_and_kb", "kb_only"]:
            logger.debug("Buscando em 'kb_store'...")
            docs_kb = self.kb_retriever.get_relevant_documents(question)
            all_relevant_docs.extend(docs_kb)
            logger.info(f"Encontrados {len(docs_kb)} documento(s) relevantes na KB.")

        if not all_relevant_docs:
            return {"answer": "Nenhum documento relevante foi encontrado no escopo de busca selecionado para responder à sua pergunta.", "source_documents": []}
        
        try:
            # A lógica da cadeia de QA permanece a mesma, usando os documentos coletados
            result = self.chat_qa_chain.invoke({"input_documents": all_relevant_docs, "question": question})
            answer = result.get("output_text", "Não foi possível gerar uma resposta.")
            
            # Formata os documentos fonte para exibição
            sources = [{"content_preview": doc.page_content[:250] + "...", **doc.metadata} for doc in all_relevant_docs]
            return {"answer": answer, "source_documents": sources}
        except Exception as e:
            logger.error(f"Erro ao executar a cadeia de chat (chat_qa_chain): {e}", exc_info=True)
            return {"answer": f"Ocorreu um erro ao processar sua pergunta: {e}", "source_documents": []}


    def summarize(self, query_for_relevance: str = "Resumo geral do caso", max_words: int = 200) -> str:
        # (Implementação como na versão anterior do pipeline.py, usando self.case_retriever, self.summarize_chain)
        # A instrução de max_words está implícita nos prompts, não é um parâmetro direto do run/invoke
        logger.info(f"Summarize (Analyzer): foco='{query_for_relevance}', max_words={max_words}")
        docs = self.case_retriever.get_relevant_documents(query_for_relevance)
        if not docs: return "Sem conteúdo para resumir em Português."
        try:
            result = self.summarize_chain.invoke({"input_documents": docs})
            return result.get("output_text", "Falha ao resumir.")
        except Exception as e: logger.error(f"Erro summarize: {e}", exc_info=True); return f"Erro ao resumir: {e}"

    def identify_risks(self, client: str, opponent: str, top_k: int = 7) -> str:
        # (Implementação como na versão anterior do pipeline.py, usando self.case_retriever, self.risk_chain)
        logger.info(f"Identificando riscos (Analyzer): cl='{client}', op='{opponent}', k={top_k}")
        docs = self.case_retriever.get_relevant_documents("")[:top_k]
        if not docs: return "Documentos insuficientes para identificar riscos."
        context = "\n\n".join([doc.page_content for doc in docs])
        try:
            result = self.risk_chain.invoke({"context": context, "client": client, "opponent": opponent})
            return result.get(self.risk_chain.output_key, result.get("text", "Não foi possível identificar riscos."))
        except Exception as e: logger.error(f"Erro identify_risks: {e}", exc_info=True); return "Erro ao identificar riscos."

    def recommend_next_steps(self, top_k: int = 7) -> str:
        # (Implementação como na versão anterior do pipeline.py, usando self.case_retriever, self.next_steps_chain)
        logger.info(f"Recomendando próximos passos (Analyzer): k={top_k}")
        docs = self.case_retriever.get_relevant_documents("")[:top_k]
        if not docs: return "Documentos insuficientes para recomendar próximos passos."
        context = "\n\n".join([doc.page_content for doc in docs])
        try:
            result = self.next_steps_chain.invoke({"context": context})
            return result.get(self.next_steps_chain.output_key, result.get("text", "Não foi possível recomendar próximos passos."))
        except Exception as e: logger.error(f"Erro recommend_next_steps: {e}", exc_info=True); return "Erro ao recomendar próximos passos."

    def _clean_llm_json_output(self, raw_llm_output: str) -> str:
        # (Implementação como na versão anterior do pipeline.py)
        logger.debug(f"Limpando LLM output para JSON. Bruto (início): '{raw_llm_output[:250]}...'")
        match_markdown = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_llm_output, re.DOTALL)
        if match_markdown:
            cleaned_str = match_markdown.group(1).strip(); logger.debug(f"JSON de bloco MD: '{cleaned_str[:200]}...'"); return cleaned_str
        stripped = raw_llm_output.strip()
        start_idx = -1
        for i, char_val in enumerate(stripped):
            if char_val in ['{', '[']: start_idx = i; break
        if start_idx != -1:
            potential_json = stripped[start_idx:]; logger.debug(f"Potencial JSON: '{potential_json[:200]}...'"); return potential_json
        logger.warning(f"Não foi possível identificar JSON em: '{raw_llm_output[:200]}'"); return stripped 

    
    def analyze_firac(self, context: str) -> Dict[str, str]:
        import sys
        from pprint import pprint
        logger.info("Iniciando análise FIRAC (Analyzer).")
        if not context.strip():
            logger.warning("Contexto FIRAC vazio."); return {k: "Contexto não fornecido." for k in self.firac_chain.output_keys}
        inputs = {"context": context}
        logger.debug(f"Input FIRAC: context='{context[:200]}...'")
        try:
            result_dict: Dict[str, str] = self.firac_chain.invoke(inputs)
            logger.info("Análise FIRAC concluída.")
            logger.info(f"[DEBUG] FIRAC passado para petição 12345:\n{json.dumps(result_dict, ensure_ascii=False, indent=2)}")
            logger.debug(f"FIRAC result: {result_dict}")  # Para depuração
            print(f"FIRAC result: {result_dict}", file=sys.stderr)  # Garante saída no terminal stderr
            return {k: result_dict.get(k, f"Seção ({k}) não gerada.") for k in self.firac_chain.output_keys}
        except Exception as e:
            logger.error(f"Erro firac_chain: {e}", exc_info=True)
            return {k: f"Erro ({k}): {e}" for k in self.firac_chain.output_keys}

