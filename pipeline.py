# pipeline.py (Versão Refatorada com LangChain Agent)
import os
import openai
from typing import List, Dict, Any, Optional

import logging
from pathlib import Path
import spacy
import json

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI # Usando as importações mais novas
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from langchain.prompts import PromptTemplate

#+ --- NOVAS IMPORTAÇÕES PARA O AGENTE ---
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# Importa nossas novas ferramentas locais
# from tools import search_arxiv_papers, fetch_web_content
#+ --- FIM DAS NOVAS IMPORTAÇÕES ---

# Importando os outros módulos do seu projeto
from ingestion_module import IngestionHandler
from analysis_module import CaseAnalyzer
from petition_module import PetitionGenerator

# from utils.text_helpers import format_cpf, format_cnpj, validate_cpf, validate_cnpj, detect_document_type
# from utils.text_helpers import extract_text, format_date_pt, clean_text, normalize_name

logger = logging.getLogger(__name__)

# Define o diretório base para os casos
CASES_DIR = Path("./cases")

class Pipeline:
    # Em pipeline.py, substitua o método __init__ da classe Pipeline por este

    def __init__(self, case_id: str):
        """
        Inicializa o pipeline para um caso específico, construindo um Agente de IA.
        """
        self.case_id = case_id
        self.case_dir = CASES_DIR / case_id
        self.case_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Orquestrador Pipeline para caso: {self.case_id} em {self.case_dir}")

        # --- Carregamento de Modelos e Componentes ---
        self.nlp = spacy.load("pt_core_news_sm")
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.5, model="gpt-4o")  # Most advanced model for best FIRAC and Petition quality
        self.openai_client = openai.OpenAI()
        
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.label_map = {"PARTES": "partes_envolvidas", "LOC": "localizacao", "ORG": "organizacao", "MONEY": "valor_monetario", "DATE": "data"}

        # --- Vector Stores ---
        self.case_store = Chroma(persist_directory=str(self.case_dir / "vectorstore"), embedding_function=self.embeddings)
        self.case_retriever = self.case_store.as_retriever(search_kwargs={"k": 7})

        # --- KB Store (para conhecimento geral, não específico do caso) ---
        # Garantindo que a lógica da KB Store esteja aqui para o kb_retriever
        kb_store_dir = Path("./kb_store")
        kb_store_dir.mkdir(parents=True, exist_ok=True)
        self.kb_store = Chroma(persist_directory=str(kb_store_dir), embedding_function=self.embeddings)
        self.kb_retriever = self.kb_store.as_retriever(search_kwargs={"k": 3})

        # --- KB de Ementas (jurisprudência) separada ---
        ementas_store_dir = Path('./ementas_kb_store')
        ementas_store_dir.mkdir(parents=True, exist_ok=True)
        self.ementas_kb_store = Chroma(persist_directory=str(ementas_store_dir), embedding_function=self.embeddings)
        self.ementas_kb_retriever = self.ementas_kb_store.as_retriever(search_kwargs={"k": 5})

        # --- Prompts para Sumarização (necessários para o CaseAnalyzer) ---
        map_prompt_template_pt = """Com base no seguinte trecho de documento, escreva um resumo conciso e informativo em PORTUGUÊS: "{text}" """ 
        self.map_prompt_pt_for_summary = PromptTemplate(template=map_prompt_template_pt, input_variables=["text"])
        combine_prompt_template_pt = """Sintetize os seguintes resumos em um resumo final coeso em PORTUGUÊS: "{text}" """ 
        self.combine_prompt_pt_for_summary = PromptTemplate(template=combine_prompt_template_pt, input_variables=["text"])

        # --- Módulos Especializados ---
        self.ingestion_handler = IngestionHandler(
            nlp_processor=self.nlp, text_splitter=self.splitter, label_map=self.label_map,
            case_store=self.case_store, kb_store=self.kb_store
        )
        self.case_analyzer = CaseAnalyzer(
            llm=self.llm,
            case_retriever=self.case_retriever,
            kb_retriever=self.kb_retriever,
            map_prompt_pt=self.map_prompt_pt_for_summary,
            combine_prompt_pt=self.combine_prompt_pt_for_summary
        )
        self.petition_generator = PetitionGenerator(llm=self.llm)

        # --- Construção do Agente de IA ---
        self.tools = [search_arxiv_papers, fetch_web_content]
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente de pesquisa jurídico.
Você tem acesso a um contexto de documentos específicos de um caso. Use este contexto PRIMEIRO.
Se a informação não estiver no contexto, use as ferramentas disponíveis.
Contexto dos documentos do caso:
---
{context}
---
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_tools_agent(self.llm, self.tools, agent_prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

        logger.info("Orquestrador Pipeline e Agente de IA inicializados.")


    # --- MÉTODO DE CHAT REFEITO ---
    def chat(self, user_query: str, chat_history: List, search_scope: str = "case") -> Dict[str, Any]:
        """Executa o agente usando diferentes escopos de busca.

        Args:
            user_query: Pergunta do usuário.
            chat_history: Histórico simples (lista de dicts role/content).
            search_scope: 'case' (default), 'kb' ou 'both'.
        """
        logger.info(f"Chat query='{user_query[:60]}...' scope={search_scope}")
        try:
            scope = (search_scope or 'case').lower()
            context_parts = []
            if scope in ("case", "both"):
                case_docs = self.case_retriever.invoke(user_query)
                context_parts.append("\n\n".join([d.page_content for d in case_docs]))
            if scope in ("kb", "both"):
                kb_docs = self.kb_retriever.invoke(user_query)
                context_parts.append("\n\n".join([d.page_content for d in kb_docs]))
            context_text = "\n\n---\n\n".join([c for c in context_parts if c]) or "(Sem contexto recuperado)"
            response = self.agent_executor.invoke({
                "input": user_query,
                "chat_history": chat_history,
                "context": context_text
            })
            return response
        except Exception as e:
            logger.error(f"Erro no chat: {e}", exc_info=True)
            return {"error": str(e)}

    # --- Strategic Analysis Methods ---
    def _collect_context(self, focus: Optional[str] = None, k_case: int = 7, k_kb: int = 3) -> str:
        try:
            parts = []
            if self.case_retriever:
                docs_case = self.case_retriever.invoke(focus or "analise geral do caso")
                parts.append("\n\n".join([d.page_content for d in docs_case]))
            if self.kb_retriever:
                docs_kb = self.kb_retriever.invoke(focus or "contexto jurídico geral")
                parts.append("\n\n".join([d.page_content for d in docs_kb]))
            context = "\n\n---\n\n".join([p for p in parts if p])
            if not context.strip():
                return "(Sem contexto disponível)"
            return context[:12000]  # limite defensivo
        except Exception as e:
            logger.error(f"Falha ao coletar contexto estratégico: {e}")
            return "(Erro ao coletar contexto)"

    def identify_legal_risks(self, focus: Optional[str] = None) -> str:
        """Gera lista estruturada de riscos legais com probabilidade, impacto e mitigação."""
        context = self._collect_context(focus)
        if context.startswith("(Sem contexto"):
            return "Nenhum documento disponível para identificar riscos. Faça upload de arquivos primeiro."
        prompt = (
            "Você é um advogado sênior. Analise o contexto do caso abaixo e identifique os PRINCIPAIS RISCOS LEGAIS e PROCESSUAIS. "
            "Responda em português com formato numerado. Para cada risco traga campos: Nome do Risco; Descrição; Probabilidade (baixa/média/alta); "
            "Impacto (baixo/médio/alto); Base Legal/Precedentes; Mitigação Recomendada; Observações. Seja conciso e objetivo.\n\n"
            f"Contexto:\n{context}\n\nRiscos:"
        )
        try:
            resp = self.llm.invoke(prompt)
            return resp.content.strip()
        except Exception as e:
            logger.error(f"Erro ao gerar riscos: {e}")
            return f"Erro ao gerar riscos: {e}"

    def suggest_next_steps(self, focus: Optional[str] = None) -> str:
        """Sugere próximos passos estratégicos e oportunidades."""
        context = self._collect_context(focus)
        if context.startswith("(Sem contexto"):
            return "Sem base documental suficiente para sugerir próximos passos."
        prompt = (
            "Atue como estrategista jurídico. Com base no contexto a seguir, liste Próximos Passos e Oportunidades. "
            "Divida em seções: (1) Ações Imediatas (2) Coleta/Produção de Provas (3) Estratégia Processual / Recursos (4) Negociação / Acordo (5) Comunicação com Cliente (6) Riscos Críticos a Monitorar. "
            "Use bullets curtos e priorize alto impacto / rápida execução.\n\n"
            f"Contexto:\n{context}\n\nPlano Estratégico:" )
        try:
            resp = self.llm.invoke(prompt)
            return resp.content.strip()
        except Exception as e:
            logger.error(f"Erro ao gerar próximos passos: {e}")
            return f"Erro ao gerar próximos passos: {e}"

    # ----------------- Resumo com Cache -----------------
    def _case_cache_dir(self) -> Path:
        d = self.case_dir / 'cache'
        d.mkdir(parents=True, exist_ok=True)
        return d

    def compute_case_digest(self) -> str:
        try:
            docs = self.list_unique_case_documents()
            if not docs:
                return 'no_docs'
            parts = [f"{d.get('source')}:{d.get('chunk_count')}" for d in docs]
            key = "|".join(sorted(parts))
            import hashlib
            return hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]
        except Exception as e:
            logger.warning(f"Falha ao computar digest: {e}")
            return 'digest_err'

    def _summary_cache_filename(self, focus: str, digest: str) -> Path:
        import hashlib
        fh = hashlib.sha1((focus or '').strip().lower().encode('utf-8')).hexdigest()[:10]
        return self._case_cache_dir() / f"summary_{digest}_{fh}.txt"

    def get_cached_summary(self, focus: str) -> Optional[str]:
        digest = self.compute_case_digest()
        path = self._summary_cache_filename(focus, digest)
        if path.exists():
            try:
                return path.read_text(encoding='utf-8')
            except Exception:
                return None
        return None

    def cache_summary(self, focus: str, content: str) -> None:
        digest = self.compute_case_digest()
        path = self._summary_cache_filename(focus, digest)
        try:
            path.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.warning(f"Não conseguiu gravar cache de resumo: {e}")

    from typing import Tuple
    def summarize_with_cache(self, query_for_relevance: str) -> 'Tuple[str, bool]':
        focus = (query_for_relevance or '').strip()
        cached = self.get_cached_summary(focus)
        if cached:
            return cached, True
        summary = self.summarize(query_for_relevance=focus or 'Resumo geral do caso')
        if summary and not summary.startswith('Erro'):
            self.cache_summary(focus, summary)
        return summary, False




    # ----------------- FIRAC Estruturado -----------------
    def _validar_firac_data(self, data: Dict[str, Any], origem: str = "FIRAC") -> None:
        campos_esperados = ["facts", "issue", "rules", "application", "conclusion"]
        
        # SANITIZAR: Converter strings em arrays quando esperado
        for campo in ["facts", "rules"]:
            if campo in data and isinstance(data[campo], str):
                logger.warning(f"[VALIDADOR {origem}] Campo '{campo}' é string, convertendo para array...")
                # Tentar quebrar por frases/parágrafos
                texto = data[campo].strip()
                if '. ' in texto:
                    data[campo] = [s.strip() + '.' for s in texto.split('. ') if s.strip()]
                else:
                    data[campo] = [texto]  # Se não tem delimitador, coloca tudo em 1 item
        
        for campo in campos_esperados:
            if campo not in data or not data[campo]:
                logger.warning(f"[VALIDADOR {origem}] Campo ausente ou vazio: {campo}")
                # Patch: Preenche campos vazios com texto genérico útil
                if campo == "facts":
                    data[campo] = ["Fato relevante não identificado no contexto."]
                elif campo == "rules":
                    data[campo] = ["Regra jurídica não identificada no contexto."]
                elif campo == "issue":
                    data[campo] = "Questão jurídica não identificada no contexto."
                elif campo == "application":
                    data[campo] = "Aplicação jurídica não identificada no contexto."
                elif campo == "conclusion":
                    data[campo] = "Conclusão não identificada no contexto."
        if all(data[c] and data[c] != "[DADO NÃO DISPONÍVEL]" for c in campos_esperados):
            logger.info(f"[VALIDADOR {origem}] Todos os campos essenciais estão presentes.")

    def generate_firac(self, focus: Optional[str] = None) -> Dict[str, Any]:
        summary, summary_cached = self.summarize_with_cache(focus or 'Resumo geral do caso')
        candidate_facts = self._extract_candidate_fact_sentences()
        focus_key = (focus or '').strip()
        firac_cache_path_json, firac_cache_path_raw = self._firac_cache_paths(focus_key)

        # PATCH: Garante contexto mínimo para FIRAC
        contexto_firac = ""
        if candidate_facts:
            contexto_firac = "\n".join(candidate_facts)
        elif summary:
            contexto_firac = summary
        else:
            contexto_firac = "O autor celebrou contrato com o réu em data não especificada."

        # Tenta cache existente de FIRAC
        if firac_cache_path_json.exists() or firac_cache_path_raw.exists():
            try:
                import json
                if firac_cache_path_json.exists():
                    data = json.loads(firac_cache_path_json.read_text(encoding='utf-8'))
                    raw = firac_cache_path_raw.read_text(encoding='utf-8') if firac_cache_path_raw.exists() else ''
                    
                    # VALIDAÇÃO: Verificar se o cache está completo e válido
                    is_cache_valid = (
                        data and 
                        isinstance(data, dict) and 
                        all(key in data for key in ['facts', 'issue', 'rules', 'application', 'conclusion']) and
                        any(data.get(key) for key in ['facts', 'issue', 'rules', 'application', 'conclusion'])
                    )
                    
                    if not is_cache_valid:
                        logger.warning("[FIRAC CACHE] Cache JSON incompleto ou vazio. Regenerando...")
                        # Continua abaixo para regenerar
                    else:
                        self._validar_firac_data(data, origem="FIRAC - CACHE")
                        logger.info(f"[FIRAC] (CACHE) Resultado: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        return {'data': data, 'raw': raw, 'cached': True}
                
                # Se só tem raw (sem JSON) ou JSON inválido, tentar parsear
                if not firac_cache_path_json.exists() or not is_cache_valid:
                    raw = firac_cache_path_raw.read_text(encoding='utf-8') if firac_cache_path_raw.exists() else ''
                    
                    if raw:
                        # Tentar parsear o raw text
                        logger.info("[FIRAC CACHE] Tentando parsear raw text para JSON...")
                        parsed_data = self._parse_raw_firac_to_json(raw)
                        
                        if parsed_data and any(parsed_data.values()):
                            # Salvar JSON parseado no cache
                            logger.info("[FIRAC CACHE] Raw text parseado com sucesso! Salvando JSON...")
                            self._cache_firac(focus_key, parsed_data, raw)
                            return {'data': parsed_data, 'raw': raw, 'cached': True}
                        else:
                            logger.warning("[FIRAC CACHE] Raw text não pôde ser parseado. Regenerando...")
                    else:
                        logger.warning("[FIRAC CACHE] Cache vazio. Regenerando...")
                    
                    # Se chegou aqui, precisa regenerar
                    # Continua para geração abaixo
                    
            except Exception as e:
                logger.warning(f"Falha ao ler FIRAC cache: {e}. Regenerando...")

        # Monta bloco de fatos candidatos para orientar o modelo
        facts_block = "\n".join([f"- {s}" for s in candidate_facts]) if candidate_facts else "(nenhum fato candidato extraído diretamente – use apenas o resumo)"
        prompt = (
    "Produza uma análise FIRAC estruturada em JSON válido UTF-8. Os campos obrigatórios são: "
    "facts (lista de strings), issue (string), rules (lista de strings), application (string), conclusion (string). "
    "Se o contexto não trouxer informações suficientes, preencha os campos com hipóteses razoáveis baseadas em casos jurídicos típicos semelhantes, sem deixar nenhum campo vazio. "
    "Se necessário, utilize exemplos genéricos, mas sempre em linguagem formal jurídica. "
    "Texto em português.\n\n"
    f"FATOS_CANDIDATOS:\n{facts_block}\n\nRESUMO:\n{summary}\n\nJSON:"
)
        try:
            logger.info(f"[DEBUG] Prompt FIRAC enviado ao LLM:\n{prompt}")
            resp = self.llm.invoke(prompt)
            raw = resp.content.strip()
            import json
            data = json.loads(raw)
            self._cache_firac(focus_key, data, raw)
            # <-- ADICIONE O LOG AQUI
            logger.info(f"[DEBUG] FIRAC GERADO pelo LLM/analysis_module.py:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
            return { 'data': data, 'raw': raw, 'cached': False, 'summary_cached': summary_cached, 'candidate_facts': candidate_facts }
        except Exception as e:
            logger.error(f"Falha FIRAC JSON: {e}")
            fallback_prompt = (
                "Gere análise FIRAC (Fatos, Questão, Regras, Aplicação, Conclusão) em seções numeradas. Português. Base no RESUMO.\n\nRESUMO:\n" + summary)
            try:
                resp2 = self.llm.invoke(fallback_prompt)
                raw_fb = resp2.content.strip()
                self._cache_firac(focus_key, None, raw_fb)
                return { 'data': None, 'raw': raw_fb, 'cached': False, 'summary_cached': summary_cached, 'candidate_facts': candidate_facts }
            except Exception as e2:
                return { 'data': None, 'raw': f'Erro ao gerar FIRAC: {e2}', 'cached': False, 'summary_cached': summary_cached, 'candidate_facts': candidate_facts }
  
    def _cache_firac(self, focus: str, data, raw: str):
        json_path, raw_path = self._firac_cache_paths(focus)
        try:
            if data:
                import json
                json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            if raw:
                raw_path.write_text(raw, encoding='utf-8')
            # Validação do FIRAC salvo no cache
            if data:
                self._validar_firac_data(data, origem="FIRAC - CACHE")
        except Exception as e:
            logger.warning(f"Não conseguiu cache FIRAC: {e}")
    
    def _parse_raw_firac_to_json(self, raw: str) -> Optional[Dict[str, str]]:
        """
        Parseia FIRAC em formato markdown/texto para dicionário JSON.
        
        Suporta formatos:
        - "**Fatos:**" ou "**Fatos**"
        - "1. **Fatos:**" (numerado)
        - Variações com acentos (Questão/Questao, Aplicação/Aplicacao, Conclusão/Conclusao)
        
        Returns:
            Dict com keys: facts, issue, rules, application, conclusion
            ou None se parsing falhar completamente
        """
        if not raw or not raw.strip():
            logger.warning("[FIRAC PARSER] Raw text está vazio")
            return None
        
        import re
        
        # Patterns robustos que capturam até o próximo marcador de seção
        facts_match = re.search(
            r'(?:\d+\.\s+)?\*\*Fatos:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*(?:Quest[aã]o|Regras|Aplica[çc][aã]o|Conclus[aã]o)|\Z)', 
            raw, 
            re.DOTALL | re.IGNORECASE
        )
        issue_match = re.search(
            r'(?:\d+\.\s+)?\*\*Quest[aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*(?:Fatos|Regras|Aplica[çc][aã]o|Conclus[aã]o)|\Z)', 
            raw, 
            re.DOTALL | re.IGNORECASE
        )
        rules_match = re.search(
            r'(?:\d+\.\s+)?\*\*Regras:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*(?:Fatos|Quest[aã]o|Aplica[çc][aã]o|Conclus[aã]o)|\Z)', 
            raw, 
            re.DOTALL | re.IGNORECASE
        )
        app_match = re.search(
            r'(?:\d+\.\s+)?\*\*Aplica[çc][aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*(?:Fatos|Quest[aã]o|Regras|Conclus[aã]o)|\Z)', 
            raw, 
            re.DOTALL | re.IGNORECASE
        )
        concl_match = re.search(
            r'(?:\d+\.\s+)?\*\*Conclus[aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*|\Z)', 
            raw, 
            re.DOTALL | re.IGNORECASE
        )
        
        result = {
            'facts': facts_match.group(1).strip() if facts_match else '',
            'issue': issue_match.group(1).strip() if issue_match else '',
            'rules': rules_match.group(1).strip() if rules_match else '',
            'application': app_match.group(1).strip() if app_match else '',
            'conclusion': concl_match.group(1).strip() if concl_match else ''
        }
        
        # Verificar se parseou algo útil
        parsed_count = sum(1 for v in result.values() if v)
        logger.info(f"[FIRAC PARSER] Successfully parsed {parsed_count}/5 fields from raw text")
        
        if parsed_count == 0:
            logger.warning("[FIRAC PARSER] Nenhum campo foi parseado! Formato do raw text pode ser incompatível")
            return None
        
        return result

    # ----------------- Extração de sentenças factuais -----------------
    def _extract_candidate_fact_sentences(self, max_docs: int = 12, max_sentences: int = 40) -> List[str]:
        """Extrai sentenças dos documentos do caso contendo palavras-chave relevantes (ex: consignado, falsificação etc.).

        Retorna lista deduplicada e curta para orientar FIRAC/petição sem gerar alucinações.
        """
        try:
            keywords = [
                'consign', 'emprest', 'assinatur', 'falsific', 'fraud', 'desconto', 'benefício', 'beneficio', 'inss',
                'aposen', 'pension', 'contrat', 'margem', 'banco', 'institui', 'financeir', 'cartão', 'cartao'
            ]
            docs_texts = []
            try:
                # Recupera documentos relevantes usando consulta neutra
                retrieved = self.case_retriever.invoke('empréstimo consignado falsificação assinatura contrato INSS')
                for d in retrieved[:max_docs]:
                    docs_texts.append(d.page_content)
            except Exception:
                pass
            if not docs_texts:
                return []
            import re
            sentences = []
            for txt in docs_texts:
                # Limite tamanho bruto para evitar explosão
                snippet = txt[:20000]
                # Quebra grosseira em sentenças
                parts = re.split(r'(?<=[.!?])\s+', snippet)
                for p in parts:
                    s = p.strip()
                    if len(s) < 25 or len(s) > 350:
                        continue
                    low = s.lower()
                    if any(k in low for k in keywords):
                        sentences.append(s)
            # Dedup conservador por lower()
            seen = set()
            ordered = []
            for s in sentences:
                key = s.lower()
                if key not in seen:
                    ordered.append(s)
                    seen.add(key)
                if len(ordered) >= max_sentences:
                    break
            return ordered
        except Exception as e:
            logger.warning(f"Falha ao extrair sentenças factuais: {e}")
            return []

    # --- FIRAC cache helpers ---
    def _firac_cache_paths(self, focus: str):
        digest = self.compute_case_digest()
        import hashlib
        fh = hashlib.sha1((focus or '').lower().encode('utf-8')).hexdigest()[:10]
        base = self._case_cache_dir() / f"firac_{digest}_{fh}"

        
        return base.with_suffix('.json'), base.with_suffix('.txt')

    
    
    # --- Backwards compatibility wrapper (legacy code chamava pipeline.summarize) ---
    def summarize(self, query_for_relevance: str = "Resumo geral do caso", max_words: int = 200) -> str:
        """Delegates to CaseAnalyzer.summarize so chamadas antigas (pipeline.summarize()) continuem funcionando.

        Args:
            query_for_relevance: Texto base para recuperar documentos relevantes.
            max_words: Mantido por compatibilidade; limite é tratado implicitamente nos prompts.
        Returns:
            str: Resumo em Português ou mensagem de erro/ausência.
        """
        try:
            if not hasattr(self, 'case_analyzer') or self.case_analyzer is None:
                return "Analisador de casos não inicializado."
            return self.case_analyzer.summarize(query_for_relevance=query_for_relevance, max_words=max_words)
        except Exception as e:
            logger.error(f"Erro no wrapper summarize: {e}", exc_info=True)
            return f"Erro ao resumir: {e}"

    # --- Seus outros métodos (processar_upload, analyze_firac, etc.) continuam aqui ---
    # Eles não precisam de alteração, pois são funcionalidades específicas.
    
    def processar_upload_de_arquivo(self, id_processo: str, nome_arquivo: str, conteudo_arquivo_bytes: bytes):
        # Este método continua perfeito como está!
        if self.case_id != id_processo: self.selecionar_caso(id_processo)
        logger.info(f"Processando upload para o caso {id_processo}: {nome_arquivo}")
        file_extension = Path(nome_arquivo).suffix.lower()
        try:
            if file_extension == ".pdf":
                self.ingestion_handler.add_pdf(conteudo_arquivo_bytes, source_name=nome_arquivo)
            elif file_extension in [".jpg", ".jpeg", ".png"]:
                self.ingestion_handler.add_image(conteudo_arquivo_bytes, source_name=nome_arquivo)
            elif file_extension == ".txt":
                # Suporte a arquivos de texto simples
                try:
                    text = conteudo_arquivo_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = conteudo_arquivo_bytes.decode('latin-1')
                    except Exception:
                        text = ''
                if not text.strip():
                    raise ValueError("Arquivo .txt vazio ou não pôde ser decodificado.")
                self.ingestion_handler.add_text_direct(text, source_name=nome_arquivo, metadata_override={"type": "text"})
            # (Futuro) Áudio / Vídeo podem ser adicionados aqui usando add_audio / add_video
            # elif file_extension in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]:
            #     self.ingestion_handler.add_audio(conteudo_arquivo_bytes, source_name=nome_arquivo, openai_client=self.openai_client)
            # elif file_extension in [".mp4", ".mov", ".avi", ".mkv"]:
            #     self.ingestion_handler.add_video(conteudo_arquivo_bytes, source_name=nome_arquivo, openai_client=self.openai_client)
            else:
                logger.warning(f"Extensão de arquivo não suportada para ingestão: {file_extension}")
                raise ValueError(f"Tipo de arquivo '{file_extension}' não suportado ainda.")
            return {"status": "sucesso", "mensagem": f"Arquivo '{nome_arquivo}' processado."}
        except Exception as e:
            logger.error(f"Falha ao processar o arquivo '{nome_arquivo}': {e}", exc_info=True)
            return {"status": "erro", "mensagem": str(e)}

    def analyze_firac(self, context: str) -> Dict[str, str]:
        return self.case_analyzer.analyze_firac(result_dict=context)
    
    
    def generate_peticao_rascunho(self, dados_ui: Dict[str, Any], result_dict: Dict[str, str]) -> str:
        logger.info(f"[DEBUG] FIRAC recebido pelo PetitionGenerator:\n{json.dumps(result_dict, ensure_ascii=False, indent=2)}")
        return self.petition_generator.generate_peticao_rascunho(dados_ui, result_dict)

    # logger.debug(f"[FIRAC] Resultado completo:\n{json.dumps(firac_results, ensure_ascii=False, indent=2)}")


    def list_case_documents_metadata(self, limit: int = 20) -> List[Dict[str, Any]]:
        # (Implementação mantida)
        logger.info(f"Listando metadados de até {limit} docs do caso (Orquestrador).")
        try:
            results = self.case_store.get(include=["metadatas"], limit=limit) 
            if results and results.get('metadatas'): return results['metadatas']
            else: 
                logger.warning("case_store.get() não retornou metadados. Tentando via retriever.")
                docs = self.case_retriever.get_relevant_documents(" ", k=limit)
                return [doc.metadata for doc in docs]
        except Exception as e: logger.error(f"Erro ao listar metadados: {e}", exc_info=True); return []


    # Em pipeline.py, dentro da classe Pipeline

    def delete_document_by_filename(self, filename: str) -> bool:
        """
        Deleta do vector store do caso todos os chunks associados a um nome de arquivo.

        Args:
            filename (str): O nome do arquivo (source) a ser deletado.

        Returns:
            bool: True se a deleção foi bem-sucedida, False caso contrário.
        """
        if not filename:
            logger.warning("Tentativa de deletar documento com nome de arquivo vazio.")
            return False

        logger.info(f"Iniciando deleção do arquivo '{filename}' do caso {self.case_id}")
        try:
            # 1. Encontrar os IDs de todos os chunks que correspondem ao nome do arquivo
            # Usamos a filtragem por metadados do ChromaDB.
            results = self.case_store.get(
                where={"source": filename},
                include=[] # Não precisamos do conteúdo, apenas dos IDs que são retornados por padrão
            )
            ids_to_delete = results.get("ids", [])

            if not ids_to_delete:
                logger.warning(f"Nenhum documento encontrado com o nome '{filename}' para deletar.")
                return True # Consideramos sucesso pois o arquivo não existe mais

            # 2. Deletar os documentos usando seus IDs
            logger.info(f"Encontrados {len(ids_to_delete)} chunks para deletar do arquivo '{filename}'.")
            self.case_store.delete(ids=ids_to_delete)
            self.case_store.persist() # Importante: persistir a mudança no disco
            logger.info(f"Deleção de '{filename}' concluída e vector store do caso persistido.")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar documento '{filename}' do caso {self.case_id}: {e}", exc_info=True)
            return False

        # Em pipeline.py, dentro da classe Pipeline

    def list_unique_case_documents(self) -> List[Dict[str, Any]]:
        """
        Busca os metadados de todos os chunks no vector store do caso,
        mas retorna uma lista de documentos únicos, sem repetição.
        """
        logger.info(f"Listando documentos únicos para o caso {self.case_id}.")
        try:
            # Pega os metadados de TODOS os chunks
            all_metadatas = self.case_store.get(include=["metadatas"]).get("metadatas", [])
            if not all_metadatas:
                return []
            
            unique_documents = {}
            # Agrupa os chunks pelo nome do arquivo (source)
            for meta in all_metadatas:
                source_name = meta.get("source")
                if source_name not in unique_documents:
                    unique_documents[source_name] = {
                        "source": source_name,
                        "type": meta.get("type", "N/A"),
                        "chunk_count": 0
                    }
                unique_documents[source_name]["chunk_count"] += 1
            
            # Retorna a lista de dicionários dos documentos únicos
            return list(unique_documents.values())
            
        except Exception as e:
            logger.error(f"Erro ao listar documentos únicos: {e}", exc_info=True)
            return []



        # --- NOVOS MÉTODOS PARA GERENCIAR E BUSCAR NA KB DE EMENTAS ---
    
    def ingest_ementas_to_kb(self, ementa_documents: List[Dict[str, str]]) -> int:
        """
        Gera embeddings para uma lista de documentos de ementas e os salva
        na base de conhecimento (vector store) de ementas.

        Args:
            ementa_documents (List[Dict[str, str]]): Lista de dicionários, cada um com 'filename' e 'content'.

        Returns:
            int: O número de documentos que foram adicionados com sucesso.
        """
        logger.info(f"Iniciando ingestão de {len(ementa_documents)} documento(s) na KB de ementas.")
        docs_to_add = []
        for doc_data in ementa_documents:
            # Para cada ementa, criamos um objeto Document do Langchain
            # Se as ementas forem muito longas, podemos usar self.splitter aqui.
            metadata = {"source": "ementa_kb_upload", "filename": doc_data.get("filename", "desconhecido")}
            doc = Document(page_content=doc_data.get("content", ""), metadata=metadata)
            docs_to_add.append(doc)
        
        if docs_to_add:
            try:
                self.ementas_kb_store.add_documents(docs_to_add)
                self.ementas_kb_store.persist()
                logger.info(f"{len(docs_to_add)} documento(s) de ementas adicionado(s) e KB de ementas persistida.")
                return len(docs_to_add)
            except Exception as e:
                logger.error(f"Erro ao adicionar ou persistir ementas na KB: {e}", exc_info=True)
                return 0
        return 0

    def find_similar_ementas(self, query_text: str, top_k: int = 5) -> List[Document]:
        """
        Usa o retriever do ChromaDB para encontrar ementas similares de forma eficiente.
        Esta busca é rápida e não consome API da OpenAI no momento da consulta.

        Args:
            query_text (str): O texto para a busca por similaridade.
            top_k (int): O número de ementas similares a retornar.

        Returns:
            List[Document]: Uma lista de objetos Document do Langchain, contendo o conteúdo
                          e metadados das ementas mais similares.
        """
        logger.info(f"Buscando {top_k} ementas similares na KB para: '{query_text[:50]}...'")
        if not self.ementas_kb_retriever:
            logger.error("Retriever da KB de Ementas não foi inicializado.")
            return []
        
        # Ajusta temporariamente o 'k' (número de resultados) do retriever para a busca atual
        self.ementas_kb_retriever.search_kwargs['k'] = top_k
        
        try:
            similar_docs = self.ementas_kb_retriever.get_relevant_documents(query_text)
            return similar_docs
        except Exception as e:
            logger.error(f"Erro ao buscar ementas similares: {e}", exc_info=True)
            return []

    def find_similar_ementas_with_scores(self, query_text: str, top_k: int = 5):
        """Retorna lista de tuplas (Document, score) usando similarity_search_with_score.

        O score retornado pelo Chroma é a distância (menor = mais similar). Para exibição
        mais intuitiva podemos converter em "similaridade" = 1 / (1 + score) se desejado
        na camada de apresentação.
        """
        try:
            return self.ementas_kb_store.similarity_search_with_score(query_text, k=top_k)
        except Exception as e:
            logger.error(f"Erro em similarity_search_with_score: {e}")
            return []

        ### ------------------------

    # Métodos de busca online que NÃO adicionam ao caso
    # NOTA: métodos fetch_live_* removidos para reduzir dependências ausentes no momento.

    # Métodos de fetch_live_* removidos/adiados enquanto integrações externas não estão prontas.

    def get_indexed_ementa_filenames(self) -> List[str]:
        """
        Busca e retorna uma lista de nomes de arquivos únicos que já foram
        indexados na Base de Conhecimento de Ementas.
        """
        logger.info("Buscando nomes de arquivos na KB de Ementas...")
        try:
            # O método .get() sem filtros retorna tudo. Pedimos apenas os metadados.
            # Isso pode ser lento se a base for gigantesca, mas para milhares de docs é aceitável.
            all_metadatas = self.ementas_kb_store.get(include=["metadatas"]).get("metadatas", [])
            if not all_metadatas:
                return []
            
            # Extrai os nomes dos arquivos e retorna uma lista única e ordenada
            filenames = sorted(list(set(meta.get("filename") for meta in all_metadatas if meta.get("filename"))))
            logger.info(f"Encontrados {len(filenames)} arquivos únicos na KB de Ementas.")
            return filenames
        except Exception as e:
            logger.error(f"Erro ao obter nomes de arquivos da KB de Ementas: {e}", exc_info=True)
            return []

    def delete_ementas_by_filename(self, filename: str) -> int:
        """
        Deleta todos os chunks de documento associados a um nome de arquivo específico
        da Base de Conhecimento de Ementas.

        Args:
            filename (str): O nome do arquivo a ser deletado.

        Returns:
            int: O número de chunks de documento que foram deletados.
        """
        if not filename:
            logger.warning("Tentativa de deletar ementa com nome de arquivo vazio.")
            return 0
            
        logger.info(f"Iniciando deleção de todos os documentos da KB de Ementas com o nome de arquivo: {filename}")
        try:
            # 1. Encontrar os IDs de todos os chunks que correspondem ao nome do arquivo
            # Usamos a filtragem por metadados do ChromaDB.
            results = self.ementas_kb_store.get(
                where={"filename": filename},
                include=[] # Não precisamos do conteúdo, apenas dos IDs que são retornados por padrão
            )
            ids_to_delete = results.get("ids", [])
            
            if not ids_to_delete:
                logger.warning(f"Nenhum documento encontrado com o nome '{filename}' para deletar.")
                return 0
            
            # 2. Deletar os documentos usando seus IDs
            logger.info(f"Encontrados {len(ids_to_delete)} chunks para deletar do arquivo '{filename}'.")
            self.ementas_kb_store._collection.delete(ids=ids_to_delete) # Usando o método delete da coleção interna
            self.ementas_kb_store.persist() # Importante: persistir a mudança
            logger.info(f"Deleção de '{filename}' concluída e KB de ementas persistida.")
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"Erro ao deletar ementas por nome de arquivo '{filename}': {e}", exc_info=True)
            return 0


    def get_global_kb_filenames(self) -> List[str]:
            """
            Busca e retorna uma lista de nomes de arquivos únicos que já foram
            indexados na Base de Conhecimento (KB) Global.

            Returns:
                List[str]: Uma lista ordenada de nomes de arquivos únicos.
            """
            logger.info("Buscando nomes de arquivos na KB Global...")
            try:
                # O método .get() sem filtros retorna todos os metadados da coleção
                # Pode ser lento se a base for gigantesca, mas é eficaz para milhares de documentos.
                all_metadatas = self.kb_store.get(include=["metadatas"]).get("metadatas", [])
                if not all_metadatas:
                    return []
                
                # Extrai os nomes dos arquivos, cria um conjunto para garantir unicidade e depois converte para uma lista ordenada
                filenames = sorted(list(set(meta.get("filename") for meta in all_metadatas if meta and meta.get("filename"))))
                logger.info(f"Encontrados {len(filenames)} arquivos únicos na KB Global.")
                return filenames
            except Exception as e:
                logger.error(f"Erro ao obter nomes de arquivos da KB Global: {e}", exc_info=True)
                return []

    def delete_from_global_kb_by_filename(self, filename: str) -> int:
        """
        Deleta da KB Global todos os chunks de documento associados a um nome de arquivo específico.

        Args:
            filename (str): O nome do arquivo a ser deletado.

        Returns:
            int: O número de chunks de documento que foram deletados.
        """
        if not filename:
            logger.warning("Tentativa de deletar da KB com nome de arquivo vazio.")
            return 0
            
        logger.info(f"Iniciando deleção da KB Global de todos os documentos com o nome de arquivo: {filename}")
        try:
            # 1. Encontrar os IDs de todos os chunks que correspondem ao nome do arquivo
            # Usamos a filtragem por metadados do ChromaDB.
            results = self.kb_store.get(
                where={"filename": filename},
                include=[] # Não precisamos do conteúdo, apenas dos IDs (retornados por padrão)
            )
            ids_to_delete = results.get("ids", [])
            
            if not ids_to_delete:
                logger.warning(f"Nenhum documento encontrado na KB Global com o nome '{filename}' para deletar.")
                return 0
            
            # 2. Deletar os documentos usando seus IDs
            logger.info(f"Encontrados {len(ids_to_delete)} chunks para deletar do arquivo '{filename}' da KB Global.")
            self.kb_store.delete(ids=ids_to_delete) # O wrapper do LangChain tem um método delete
            self.kb_store.persist() # Importante: persistir a mudança no disco
            logger.info(f"Deleção de '{filename}' concluída e KB Global persistida.")
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"Erro ao deletar da KB Global por nome de arquivo '{filename}': {e}", exc_info=True)
            return 0

# Em pipeline.py, dentro da sua classe Pipeline

    # Em pipeline.py, dentro da sua classe Pipeline

   # Em pipeline.py, dentro da sua classe Pipeline

    # --- MÉTODO get_final_response 100% Assíncrono ---
    # Método assíncrono avançado removido para simplificação neste estágio.
    

# Bloco if __name__ == "__main__": para testes do orquestrador pode ser adicionado aqui,
# similar ao que existia, mas agora chamando os métodos do Pipeline que delegam.
if __name__ == '__main__':
    # Execução de teste simplificada ou omitida para ambiente de produção/web.
    logger.info("Pipeline módulo executado diretamente - nenhum teste automático configurado.")

