# analysis_module.py
import logging
import json
import re  # Para _clean_llm_json_output
from typing import Any, Dict, List, Protocol

from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class RetrieverProtocol(Protocol):
    def get_relevant_documents(self, query: str) -> List[Any]:
        ...


class LLMProtocol(Protocol):
    def invoke(self, input: Any, **kwargs: Any) -> Any:
        ...

class CaseAnalyzer:
    def __init__(self, llm: LLMProtocol, 
                 case_retriever: RetrieverProtocol,
                 kb_retriever: RetrieverProtocol,
                 map_prompt_pt: PromptTemplate, # Passando os prompts de resumo
                 combine_prompt_pt: PromptTemplate):
        self.llm = llm
        self.case_retriever = case_retriever
        self.kb_retriever = kb_retriever

        self.map_prompt_pt_for_summary = map_prompt_pt
        self.combine_prompt_pt_for_summary = combine_prompt_pt
     
        # Inicializa prompts e chains de análise e FIRAC
        self._initialize_analysis_prompts_and_chains()
        self._initialize_firac_prompts_and_chains()

    def _doc_to_text(self, doc: Any) -> str:
        if doc is None:
            return ""
        page_content = getattr(doc, "page_content", None)
        if isinstance(page_content, str):
            return page_content
        if isinstance(doc, dict):
            return str(doc.get("page_content") or doc.get("content") or doc)
        return str(doc)

    def _extract_text_from_llm_response(self, response: Any) -> str:
        """Normaliza respostas do LangChain em texto simples."""
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(parts).strip()

        return str(content).strip()

    def _invoke_prompt(self, prompt: PromptTemplate, input_data: Dict[str, Any]) -> str:
        rendered = prompt.format(**input_data)
        resp = self.llm.invoke(rendered)
        return self._extract_text_from_llm_response(resp)

    def _retrieve(self, retriever: Any, query: str) -> List[Any]:
        """Compat: retrievers novos usam .invoke(); antigos usam get_relevant_documents()."""
        if retriever is None:
            return []
        if hasattr(retriever, "invoke"):
            try:
                result = retriever.invoke(query)
                return list(result) if isinstance(result, list) else [result]
            except Exception:
                pass
        if hasattr(retriever, "get_relevant_documents"):
            return retriever.get_relevant_documents(query)
        return []

    def _initialize_analysis_prompts_and_chains(self):
        # (Código dos Prompts RISK, NEXT_STEPS
        #  e suas respectivas LLMChains, como na versão anterior do pipeline.py __init__)
        self.RISK_PROMPT = PromptTemplate(input_variables=["context", "client", "opponent"], template="Você é um advogado analisando um caso para o cliente {client} contra a parte oponente {opponent}...\nContexto dos Documentos do Caso:\n{context}\n\nFormato da resposta (use markdown):...") # Template completo omitido por brevidade
        self.NEXT_STEPS_PROMPT = PromptTemplate(input_variables=["context"], template="Você é um advogado consultor...\nContexto dos Documentos do Caso:\n{context}\n\nFormato da Resposta (use markdown):...")
        
    def _initialize_firac_prompts_and_chains(self):
        # (Código dos Prompts FACTS, ISSUE, RULE, APPLICATION, CONCLUSION
        #  e suas respectivas LLMChains, e o firac_chain (SequentialChain),
        #  como na versão anterior do pipeline.py __init__)
        self.FACTS_PROMPT = PromptTemplate(input_variables=["context"], template="Você é um assistente jurídico...\nContexto do Caso:\n{context}\n\nFATOS JURIDICAMENTE RELEVANTES:")
        self.ISSUE_PROMPT = PromptTemplate(input_variables=["facts"], template="Considerando os seguintes fatos...\n{facts}\n\nQUESTÃO(ÕES) JURÍDICA(S) CENTRAL(AIS):")
        self.RULE_PROMPT = PromptTemplate(input_variables=["issue", "context"], template="Para a(s) seguinte(s) questão(ões)...\n{issue}\n\nE contexto:\n{context}\n\nREGRAS (NORMAS E JURISPRUDÊNCIA) APLICÁVEIS:")
        self.APPLICATION_PROMPT = PromptTemplate(input_variables=["facts", "rules", "issue"], template="Analise a aplicação...\nQuestão: {issue}\n\nFatos:\n{facts}\n\nRegras:\n{rules}\n\nAPLICAÇÃO DAS REGRAS AOS FATOS:")
        self.CONCLUSION_PROMPT = PromptTemplate(input_variables=["application", "issue"], template="Com base na análise para a questão \"{issue}\":\n{application}\n\nCONCLUSÃO E ESTRATÉGIA INICIAL:")
        self.firac_output_keys = ["facts", "issue", "rules", "application", "conclusion"]

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
            docs_case = self._retrieve(self.case_retriever, question)
            all_relevant_docs.extend(docs_case)
            logger.info(f"Encontrados {len(docs_case)} documento(s) relevantes no caso.")
            
        if search_scope in ["case_and_kb", "kb_only"]:
            logger.debug("Buscando em 'kb_store'...")
            docs_kb = self._retrieve(self.kb_retriever, question)
            all_relevant_docs.extend(docs_kb)
            logger.info(f"Encontrados {len(docs_kb)} documento(s) relevantes na KB.")

        if not all_relevant_docs:
            return {"answer": "Nenhum documento relevante foi encontrado no escopo de busca selecionado para responder à sua pergunta.", "source_documents": []}
        
        try:
            context = "\n\n".join(self._doc_to_text(doc) for doc in all_relevant_docs)
            chat_prompt = (
                "Você é um assistente jurídico. Use PRIORITARIAMENTE o contexto fornecido. "
                "Se não houver informação suficiente no contexto, explique claramente a limitação e responda com cautela.\n\n"
                "CONTEXTO:\n{context}\n\n"
                "PERGUNTA:\n{question}\n\n"
                "RESPOSTA (português formal, objetivo):"
            )
            resp = self.llm.invoke(chat_prompt.format(context=context, question=question))
            answer = self._extract_text_from_llm_response(resp) or "Não foi possível gerar uma resposta."
            
            # Formata os documentos fonte para exibição
            sources: List[Dict[str, Any]] = []
            for doc in all_relevant_docs:
                preview = (self._doc_to_text(doc) or "")[:250] + "..."
                metadata = getattr(doc, "metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {"metadata": str(metadata)}
                sources.append({"content_preview": preview, **metadata})
            return {"answer": answer, "source_documents": sources}
        except Exception as e:
            logger.error(f"Erro ao executar a cadeia de chat (chat_qa_chain): {e}", exc_info=True)
            return {"answer": f"Ocorreu um erro ao processar sua pergunta: {e}", "source_documents": []}


    def summarize(self, query_for_relevance: str = "Resumo geral do caso", max_words: int = 200) -> str:
        logger.info(f"Summarize (Analyzer): foco='{query_for_relevance}', max_words={max_words}")
        docs = self._retrieve(self.case_retriever, query_for_relevance)
        if not docs: return "Sem conteúdo para resumir em Português."
        try:
            partials: List[str] = []
            for doc in docs:
                text = self._doc_to_text(doc)
                if not text.strip():
                    continue
                partial = self._invoke_prompt(self.map_prompt_pt_for_summary, {"text": text})
                if partial:
                    partials.append(partial)

            combined_input = "\n\n".join(partials) if partials else "\n\n".join(self._doc_to_text(d) for d in docs)
            combine_prompt = (
                self.combine_prompt_pt_for_summary.format(text=combined_input)
                + f"\n\nLimite de tamanho: no máximo {max_words} palavras."
            )
            resp = self.llm.invoke(combine_prompt)
            return self._extract_text_from_llm_response(resp) or "Falha ao resumir."
        except Exception as e:
            logger.error(f"Erro summarize: {e}", exc_info=True)
            return f"Erro ao resumir: {e}"

    def identify_risks(self, client: str, opponent: str, top_k: int = 7) -> str:
        # (Implementação como na versão anterior do pipeline.py, usando self.case_retriever, self.risk_chain)
        logger.info(f"Identificando riscos (Analyzer): cl='{client}', op='{opponent}', k={top_k}")
        docs = self._retrieve(self.case_retriever, "")[:top_k]
        if not docs: return "Documentos insuficientes para identificar riscos."
        context = "\n\n".join([doc.page_content for doc in docs])
        try:
            return self._invoke_prompt(self.RISK_PROMPT, {"context": context, "client": client, "opponent": opponent}) or "Não foi possível identificar riscos."
        except Exception as e: logger.error(f"Erro identify_risks: {e}", exc_info=True); return "Erro ao identificar riscos."

    def recommend_next_steps(self, top_k: int = 7) -> str:
        # (Implementação como na versão anterior do pipeline.py, usando self.case_retriever, self.next_steps_chain)
        logger.info(f"Recomendando próximos passos (Analyzer): k={top_k}")
        docs = self._retrieve(self.case_retriever, "")[:top_k]
        if not docs: return "Documentos insuficientes para recomendar próximos passos."
        context = "\n\n".join([doc.page_content for doc in docs])
        try:
            return self._invoke_prompt(self.NEXT_STEPS_PROMPT, {"context": context}) or "Não foi possível recomendar próximos passos."
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
            logger.warning("Contexto FIRAC vazio."); return {k: "Contexto não fornecido." for k in self.firac_output_keys}
        logger.debug(f"Input FIRAC: context='{context[:200]}...'")
        try:
            facts = self._invoke_prompt(self.FACTS_PROMPT, {"context": context})
            issue = self._invoke_prompt(self.ISSUE_PROMPT, {"facts": facts})
            rules = self._invoke_prompt(self.RULE_PROMPT, {"issue": issue, "context": context})
            application = self._invoke_prompt(
                self.APPLICATION_PROMPT,
                {"facts": facts, "rules": rules, "issue": issue},
            )
            conclusion = self._invoke_prompt(
                self.CONCLUSION_PROMPT,
                {"application": application, "issue": issue},
            )
            result_dict: Dict[str, str] = {
                "facts": facts,
                "issue": issue,
                "rules": rules,
                "application": application,
                "conclusion": conclusion,
            }
            logger.info("Análise FIRAC concluída.")
            logger.info(f"[DEBUG] FIRAC passado para petição 12345:\n{json.dumps(result_dict, ensure_ascii=False, indent=2)}")
            logger.debug(f"FIRAC result: {result_dict}")  # Para depuração
            print(f"FIRAC result: {result_dict}", file=sys.stderr)  # Garante saída no terminal stderr
            return {k: result_dict.get(k, f"Seção ({k}) não gerada.") for k in self.firac_output_keys}
        except Exception as e:
            logger.error(f"Erro firac_chain: {e}", exc_info=True)
            return {k: f"Erro ({k}): {e}" for k in self.firac_output_keys}

