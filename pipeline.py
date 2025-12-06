# pipeline.py (Versão Refatorada com suporte a multi-tenant)
import os
from flask import g
import openai
from typing import List, Dict, Any, Optional, Tuple

import logging
from pathlib import Path
import spacy
import json
import hashlib
import re

from werkzeug.utils import secure_filename
import hashlib
# from app.services.openai_client import client as openai_client  # Removido: import não resolvido

from cadastro_manager import CadastroManager

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI  # Usando as importações mais novas
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate

# --- NOVAS IMPORTAÇÕES PARA O AGENTE (algumas não mais usadas diretamente, mas mantidas p/ compat) ---
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Importando os outros módulos do seu projeto
from ingestion_module import IngestionHandler
from analysis_module import CaseAnalyzer
from petition_module import PetitionGenerator

logger = logging.getLogger(__name__)

# Diretório base para os casos (por tenant)
CASES_DIR = Path("./cases")

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".ogg", ".aac"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".wmv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}

class Pipeline:
    def __init__(
        self,
        case_id: str,
        ingestion_handler: IngestionHandler | None = None,
        openai_client: openai.OpenAI | None = None,
        base_cases_dir: Path | None = None,
        tenant_id: str | None = None,
    ):
        """
        Inicializa o pipeline para um caso específico, com suporte multi-tenant.

        Args:
            case_id: identificador lógico do processo (id_processo).
            tenant_id: identificador do tenant (g.tenant_id) para isolar diretórios.
        """
        self.case_id = case_id
        self.ingestion_handler = ingestion_handler
        self.openai_client = openai_client
        self.base_cases_dir = base_cases_dir
        self.tenant_id = tenant_id


        # --- Diretórios por tenant ---
        tenant_segment = str(tenant_id) if tenant_id else "default"

        # Diretório base do tenant
        self.base_dir = CASES_DIR / tenant_segment
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Diretório específico do caso
        self.case_dir = self.base_dir / case_id
        self.case_dir.mkdir(parents=True, exist_ok=True)

        # Diretório de cache do caso
        self._cache_dir = self.case_dir / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Orquestrador Pipeline para caso: {self.case_id} "
            f"(tenant={tenant_segment}) em {self.case_dir}"
        )

        # --- Modelos e componentes básicos ---
        self.nlp = spacy.load("pt_core_news_sm")
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.5, model="gpt-4o")
        self.openai_client = openai.OpenAI()

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        self.label_map = {
            "PARTES": "partes_envolvidas",
            "LOC": "localizacao",
            "ORG": "organizacao",
            "MONEY": "valor_monetario",
            "DATE": "data"
        }

        # --- Vector Store do CASO ---
        self.case_store = Chroma(
            persist_directory=str(self.case_dir / "vectorstore"),
            embedding_function=self.embeddings
        )
        self.case_retriever = self.case_store.as_retriever(
            search_kwargs={"k": 7}
        )

        # --- KB Global (pode ser segmentada por tenant também, se desejar) ---
        kb_store_dir = Path("./kb_store") / tenant_segment
        kb_store_dir.mkdir(parents=True, exist_ok=True)
        self.kb_store = Chroma(
            persist_directory=str(kb_store_dir),
            embedding_function=self.embeddings
        )
        self.kb_retriever = self.kb_store.as_retriever(
            search_kwargs={"k": 3}
        )

        # --- KB de Ementas (jurisprudência), também por tenant ---
        ementas_store_dir = Path("./ementas_kb_store") / tenant_segment
        ementas_store_dir.mkdir(parents=True, exist_ok=True)
        self.ementas_kb_store = Chroma(
            persist_directory=str(ementas_store_dir),
            embedding_function=self.embeddings
        )
        self.ementas_kb_retriever = self.ementas_kb_store.as_retriever(
            search_kwargs={"k": 5}
        )

        # --- Prompts para sumarização (CaseAnalyzer) ---
        map_prompt_template_pt = (
            "Com base no seguinte trecho de documento, escreva um resumo conciso "
            'e informativo em PORTUGUÊS: "{text}" '
        )
        self.map_prompt_pt_for_summary = PromptTemplate(
            template=map_prompt_template_pt,
            input_variables=["text"]
        )

        combine_prompt_template_pt = (
            "Sintetize os seguintes resumos em um resumo final coeso em PORTUGUÊS: "
            '"{text}" '
        )
        self.combine_prompt_pt_for_summary = PromptTemplate(
            template=combine_prompt_template_pt,
            input_variables=["text"]
        )

        # --- Módulos especializados ---
        self.ingestion_handler = IngestionHandler(
            nlp_processor=self.nlp,
            text_splitter=self.splitter,
            label_map=self.label_map,
            case_store=self.case_store,
            kb_store=self.kb_store,
        )

        self.case_analyzer = CaseAnalyzer(
            llm=self.llm,
            case_retriever=self.case_retriever,
            kb_retriever=self.kb_retriever,
            map_prompt_pt=self.map_prompt_pt_for_summary,
            combine_prompt_pt=self.combine_prompt_pt_for_summary,
        )

        self.petition_generator = PetitionGenerator(llm=self.llm)
              # --- CadastroManager para persistência em PostgreSQL ---
        self.cadastro_manager = CadastroManager(tenant_id=self.tenant_id)


        # --- Prompt simples de CHAT (sem ferramentas externas por enquanto) ---
        self.chat_system_prompt = (
            "Você é um assistente de pesquisa jurídico especializado em Direito "
            "do Consumidor, contratos bancários e casos envolvendo empréstimo "
            "consignado e fraudes.\n\n"
            "Use PRIMEIRO o contexto dos documentos do caso. "
            "Se algo não estiver no contexto, responda com base no conhecimento "
            "jurídico geral, mas sempre de forma cautelosa e em português formal.\n\n"
            "Contexto a seguir:\n---\n{context}\n---\n"
        )

        logger.info("Orquestrador Pipeline inicializado com sucesso.")

    # ======================================================================
    # MÉTODO DE CHAT (compatível com /processos/ui/<id_processo>/chat)
    # ======================================================================
    def chat(
        self,
        user_query: str,
        chat_history: List[Dict[str, str]],
        search_scope: str = "case",
    ) -> Dict[str, Any]:
        """
        Executa um chat sobre o caso usando RAG simples (case / kb / both).

        Args:
            user_query: Pergunta do usuário.
            chat_history: Lista de mensagens anteriores, ex:
                [{'role': 'user','content': '...'}, {'role': 'assistant','content': '...'}]
            search_scope: 'case' (default), 'kb' ou 'both'.

        Returns:
            Dict com pelo menos a chave 'output' (string), compatível com processos.ui_chat.
        """
        logger.info(
            f"[CHAT] query='{user_query[:80]}...' scope={search_scope} case={self.case_id}"
        )
        try:
            scope = (search_scope or "case").lower()
            context_parts: List[str] = []

            if scope in ("case", "both"):
                try:
                    case_docs = self.case_retriever.invoke(user_query)
                    context_parts.append(
                        "\n\n".join([d.page_content for d in case_docs])
                    )
                except Exception as e:
                    logger.warning(f"[CHAT] Falha ao recuperar docs do caso: {e}")

            if scope in ("kb", "both"):
                try:
                    kb_docs = self.kb_retriever.invoke(user_query)
                    context_parts.append(
                        "\n\n".join([d.page_content for d in kb_docs])
                    )
                except Exception as e:
                    logger.warning(f"[CHAT] Falha ao recuperar docs da KB: {e}")

            context_text = (
                "\n\n---\n\n".join([c for c in context_parts if c])
                or "(Sem contexto recuperado para esta pergunta.)"
            )

            # Monta prompt único para o LLM
            history_str = ""
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_str += f"{role.upper()}: {content}\n"

            full_prompt = (
                self.chat_system_prompt.format(context=context_text)
                + "\n\n"
                + "HISTÓRICO DO CHAT:\n"
                + history_str
                + "\n\n"
                + f"USUÁRIO: {user_query}\nASSISTENTE:"
            )

            resp = self.llm.invoke(full_prompt)
            answer = resp.content.strip()
            return {"output": answer}

        except Exception as e:
            logger.error(f"Erro no chat: {e}", exc_info=True)
            return {"error": str(e)}

    # ======================================================================
    # COLETA DE CONTEXTO E ANÁLISES ESTRATÉGICAS (RISCOS, PRÓXIMOS PASSOS)
    # ======================================================================
    def _collect_context(
        self,
        focus: Optional[str] = None,
        k_case: int = 7,
        k_kb: int = 3,
    ) -> str:
        """
        Coleta contexto combinando documentos do caso + KB global.
        """
        try:
            parts = []

            if self.case_retriever:
                docs_case = self.case_retriever.invoke(
                    focus or "analise geral do caso"
                )
                parts.append(
                    "\n\n".join([d.page_content for d in docs_case[:k_case]])
                )

            if self.kb_retriever:
                docs_kb = self.kb_retriever.invoke(
                    focus or "contexto jurídico geral"
                )
                parts.append(
                    "\n\n".join([d.page_content for d in docs_kb[:k_kb]])
                )

            context = "\n\n---\n\n".join([p for p in parts if p])

            if not context.strip():
                return "(Sem contexto disponível)"

            # Limite defensivo de tamanho
            return context[:12000]

        except Exception as e:
            logger.error(f"Falha ao coletar contexto estratégico: {e}")
            return "(Erro ao coletar contexto)"

    def identify_legal_risks(self, focus: Optional[str] = None) -> str:
        """
        Gera lista estruturada de riscos legais com probabilidade, impacto e mitigação.
        Usado em /processos/ui/<id_processo>/analise/riscos
        """
        context = self._collect_context(focus)
        if context.startswith("(Sem contexto"):
            return "Nenhum documento disponível para identificar riscos. Faça upload de arquivos primeiro."

        prompt = (
            "Você é um advogado sênior. Analise o contexto do caso abaixo e "
            "identifique os PRINCIPAIS RISCOS LEGAIS e PROCESSUAIS. "
            "Responda em português com formato numerado. Para cada risco traga "
            "campos: Nome do Risco; Descrição; Probabilidade (baixa/média/alta); "
            "Impacto (baixo/médio/alto); Base Legal/Precedentes; Mitigação "
            "Recomendada; Observações. Seja conciso e objetivo.\n\n"
            f"Contexto:\n{context}\n\nRiscos:"
        )
        try:
            resp = self.llm.invoke(prompt)
            return resp.content.strip()
        except Exception as e:
            logger.error(f"Erro ao gerar riscos: {e}")
            return f"Erro ao gerar riscos: {e}"

    def suggest_next_steps(self, focus: Optional[str] = None) -> str:
        """
        Sugere próximos passos estratégicos e oportunidades.
        Usado em /processos/ui/<id_processo>/analise/proximos_passos
        """
        context = self._collect_context(focus)
        if context.startswith("(Sem contexto"):
            return "Sem base documental suficiente para sugerir próximos passos."

        prompt = (
            "Atue como estrategista jurídico. Com base no contexto a seguir, "
            "liste Próximos Passos e Oportunidades. "
            "Divida em seções: (1) Ações Imediatas (2) Coleta/Produção de Provas "
            "(3) Estratégia Processual / Recursos (4) Negociação / Acordo "
            "(5) Comunicação com Cliente (6) Riscos Críticos a Monitorar. "
            "Use bullets curtos e priorize alto impacto / rápida execução.\n\n"
            f"Contexto:\n{context}\n\nPlano Estratégico:"
        )
        try:
            resp = self.llm.invoke(prompt)
            return resp.content.strip()
        except Exception as e:
            logger.error(f"Erro ao gerar próximos passos: {e}")
            return f"Erro ao gerar próximos passos: {e}"

    # ======================================================================
    # CACHE DE RESUMO DO CASO
    # ======================================================================
    def _case_cache_dir(self) -> Path:
        d = self.case_dir / "cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def compute_case_digest(self) -> str:
        """
        Gera um "hash" curto que representa o conjunto de documentos do caso.
        Se os docs mudarem, o digest muda → invalida cache antigo.
        """
        try:
            docs = self.list_unique_case_documents()
            if not docs:
                return "no_docs"

            parts = [
                f"{d.get('source')}:{d.get('chunk_count')}"
                for d in docs
            ]
            key = "|".join(sorted(parts))
            return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        except Exception as e:
            logger.warning(f"Falha ao computar digest: {e}")
            return "digest_err"

    def _summary_cache_filename(self, focus: str, digest: str) -> Path:
        fh = hashlib.sha1(
            (focus or "").strip().lower().encode("utf-8")
        ).hexdigest()[:10]
        return self._case_cache_dir() / f"summary_{digest}_{fh}.txt"

    def get_cached_summary(self, focus: str) -> Optional[str]:
        digest = self.compute_case_digest()
        path = self._summary_cache_filename(focus, digest)
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def cache_summary(self, focus: str, content: str) -> None:
        digest = self.compute_case_digest()
        path = self._summary_cache_filename(focus, digest)
        try:
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Não conseguiu gravar cache de resumo: {e}")

    def summarize_with_cache(self, query_for_relevance: str) -> Tuple[str, bool]:
        """
        Wrapper usado em /processos/ui/<id_processo>/resumo.
        Retorna (resumo, from_cache: bool).
        """
        focus = (query_for_relevance or "").strip()
        cached = self.get_cached_summary(focus)
        if cached:
            return cached, True

        summary = self.summarize(
            query_for_relevance=focus or "Resumo geral do caso"
        )
        if summary and not summary.startswith("Erro"):
            self.cache_summary(focus, summary)

        return summary, False

    # ======================================================================
    # RESUMO (delegando ao CaseAnalyzer para compatibilidade)
    # ======================================================================
    def summarize(
        self,
        query_for_relevance: str = "Resumo geral do caso",
        max_words: int = 200,
    ) -> str:
        """
        Delegado ao CaseAnalyzer.summarize, para manter compatibilidade
        com código legado (pipeline.summarize()).
        """
        try:
            if not hasattr(self, "case_analyzer") or self.case_analyzer is None:
                return "Analisador de casos não inicializado."
            return self.case_analyzer.summarize(
                query_for_relevance=query_for_relevance,
                max_words=max_words,
            )
        except Exception as e:
            logger.error(f"Erro no wrapper summarize: {e}", exc_info=True)
            return f"Erro ao resumir: {e}"

    # ======================================================================
    # FIRAC E CACHE DE FIRAC
    # ======================================================================
    def _validar_firac_data(
        self,
        data: Dict[str, Any],
        origem: str = "FIRAC",
    ) -> None:
        """
        Sanitiza e valida o dicionário FIRAC.
        Garante que todos os campos essenciais existam.
        """
        campos_esperados = [
            "facts",
            "issue",
            "rules",
            "application",
            "conclusion",
        ]

        # Converter strings em arrays para facts/rules se necessário
        for campo in ["facts", "rules"]:
            if campo in data and isinstance(data[campo], str):
                logger.warning(
                    f"[VALIDADOR {origem}] Campo '{campo}' é string, "
                    "convertendo para array..."
                )
                texto = data[campo].strip()
                if ". " in texto:
                    data[campo] = [
                        s.strip() + "."
                        for s in texto.split(". ")
                        if s.strip()
                    ]
                else:
                    data[campo] = [texto]

        for campo in campos_esperados:
            if campo not in data or not data[campo]:
                logger.warning(
                    f"[VALIDADOR {origem}] Campo ausente ou vazio: {campo}"
                )
                if campo == "facts":
                    data[campo] = ["Fato relevante não identificado no contexto."]
                elif campo == "rules":
                    data[campo] = ["Regra jurídica não identificada no contexto."]
                elif campo == "issue":
                    data[campo] = "Questão jurídica não identificada no contexto."
                elif campo == "application":
                    data[campo] = (
                        "Aplicação jurídica não identificada no contexto."
                    )
                elif campo == "conclusion":
                    data[campo] = "Conclusão não identificada no contexto."

        if all(data[c] and data[c] != "[DADO NÃO DISPONÍVEL]" for c in campos_esperados):
            logger.info(f"[VALIDADOR {origem}] Todos os campos essenciais estão presentes.")

    def _firac_cache_paths(self, focus: str):
        digest = self.compute_case_digest()
        fh = hashlib.sha1(
            (focus or "").lower().encode("utf-8")
        ).hexdigest()[:10]
        base = self._case_cache_dir() / f"firac_{digest}_{fh}"
        return base.with_suffix(".json"), base.with_suffix(".txt")

    def _cache_firac(self, focus: str, data, raw: str):
        json_path, raw_path = self._firac_cache_paths(focus)
        try:
            if data:
                json_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            if raw:
                raw_path.write_text(raw, encoding="utf-8")
            if data:
                self._validar_firac_data(data, origem="FIRAC - CACHE")
        except Exception as e:
            logger.warning(f"Não conseguiu cache FIRAC: {e}")

    def _parse_raw_firac_to_json(self, raw: str) -> Optional[Dict[str, str]]:
        """
        Converte texto FIRAC (markdown) em dicionário JSON.
        Suporta seções em negrito: **Fatos**, **Questão**, **Regras**, **Aplicação**, **Conclusão**.
        """
        if not raw or not raw.strip():
            logger.warning("[FIRAC PARSER] Raw text está vazio")
            return None

        # Patterns robustos
        facts_match = re.search(
            r'(?:\d+\.\s+)?\*\*Fatos:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*'
            r'(?:Quest[aã]o|Regras|Aplica[çc][aã]o|Conclus[aã]o)|\Z)',
            raw,
            re.DOTALL | re.IGNORECASE,
        )
        issue_match = re.search(
            r'(?:\d+\.\s+)?\*\*Quest[aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*'
            r'(?:Fatos|Regras|Aplica[çc][aã]o|Conclus[aã]o)|\Z)',
            raw,
            re.DOTALL | re.IGNORECASE,
        )
        rules_match = re.search(
            r'(?:\d+\.\s+)?\*\*Regras:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*'
            r'(?:Fatos|Quest[aã]o|Aplica[çc][aã]o|Conclus[aã]o)|\Z)',
            raw,
            re.DOTALL | re.IGNORECASE,
        )
        app_match = re.search(
            r'(?:\d+\.\s+)?\*\*Aplica[çc][aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*'
            r'(?:Fatos|Quest[aã]o|Regras|Conclus[aã]o)|\Z)',
            raw,
            re.DOTALL | re.IGNORECASE,
        )
        concl_match = re.search(
            r'(?:\d+\.\s+)?\*\*Conclus[aã]o:?\*\*\s*(.*?)(?=\n\s*(?:\d+\.\s+)?\*\*|\Z)',
            raw,
            re.DOTALL | re.IGNORECASE,
        )

        result = {
            "facts": facts_match.group(1).strip() if facts_match else "",
            "issue": issue_match.group(1).strip() if issue_match else "",
            "rules": rules_match.group(1).strip() if rules_match else "",
            "application": app_match.group(1).strip() if app_match else "",
            "conclusion": concl_match.group(1).strip() if concl_match else "",
        }

        parsed_count = sum(1 for v in result.values() if v)
        logger.info(
            f"[FIRAC PARSER] Successfully parsed {parsed_count}/5 fields from raw text"
        )

        if parsed_count == 0:
            logger.warning(
                "[FIRAC PARSER] Nenhum campo foi parseado! Formato do raw text pode ser incompatível"
            )
            return None

        return result

    def _extract_candidate_fact_sentences(
        self,
        max_docs: int = 12,
        max_sentences: int = 40,
    ) -> List[str]:
        """
        Extrai sentenças factuais dos documentos do caso contendo palavras-chave
        relevantes (ex: consignado, falsificação, etc.) para orientar FIRAC/petição.
        """
        try:
            keywords = [
                "consign",
                "emprest",
                "assinatur",
                "falsific",
                "fraud",
                "desconto",
                "benefício",
                "beneficio",
                "inss",
                "aposen",
                "pension",
                "contrat",
                "margem",
                "banco",
                "institui",
                "financeir",
                "cartão",
                "cartao",
            ]
            docs_texts = []
            try:
                retrieved = self.case_retriever.invoke(
                    "empréstimo consignado falsificação assinatura contrato INSS"
                )
                for d in retrieved[:max_docs]:
                    docs_texts.append(d.page_content)
            except Exception:
                pass

            if not docs_texts:
                return []

            sentences = []
            for txt in docs_texts:
                snippet = txt[:20000]
                parts = re.split(r"(?<=[.!?])\s+", snippet)
                for p in parts:
                    s = p.strip()
                    if len(s) < 25 or len(s) > 350:
                        continue
                    low = s.lower()
                    if any(k in low for k in keywords):
                        sentences.append(s)

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

    def generate_firac(self, focus: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera (ou reutiliza do cache) uma análise FIRAC estruturada:
        facts, issue, rules, application, conclusion.
        Usado em /processos/ui/<id_processo>/analise/firac e geração de petição.
        """
        summary, summary_cached = self.summarize_with_cache(
            focus or "Resumo geral do caso"
        )
        candidate_facts = self._extract_candidate_fact_sentences()
        focus_key = (focus or "").strip()
        firac_cache_path_json, firac_cache_path_raw = self._firac_cache_paths(
            focus_key
        )

        contexto_firac = ""
        if candidate_facts:
            contexto_firac = "\n".join(candidate_facts)
        elif summary:
            contexto_firac = summary
        else:
            contexto_firac = (
                "O autor celebrou contrato com o réu em data não especificada."
            )

        # Tentar ler do cache
        if firac_cache_path_json.exists() or firac_cache_path_raw.exists():
            try:
                data = None
                raw = ""

                if firac_cache_path_json.exists():
                    data = json.loads(
                        firac_cache_path_json.read_text(encoding="utf-8")
                    )
                    raw = (
                        firac_cache_path_raw.read_text(encoding="utf-8")
                        if firac_cache_path_raw.exists()
                        else ""
                    )

                    is_cache_valid = (
                        data
                        and isinstance(data, dict)
                        and all(
                            key in data
                            for key in [
                                "facts",
                                "issue",
                                "rules",
                                "application",
                                "conclusion",
                            ]
                        )
                        and any(
                            data.get(key)
                            for key in [
                                "facts",
                                "issue",
                                "rules",
                                "application",
                                "conclusion",
                            ]
                        )
                    )

                    if is_cache_valid:
                        self._validar_firac_data(
                            data, origem="FIRAC - CACHE"
                        )
                        logger.info(
                            f"[FIRAC] (CACHE) Resultado: "
                            f"{json.dumps(data, ensure_ascii=False, indent=2)}"
                        )
                        return {
                            "data": data,
                            "raw": raw,
                            "cached": True,
                        }
                    else:
                        logger.warning(
                            "[FIRAC CACHE] Cache JSON incompleto ou vazio. Regenerando..."
                        )

                # Se só houver raw, tentar parsear
                if firac_cache_path_raw.exists():
                    raw = firac_cache_path_raw.read_text(encoding="utf-8")
                    if raw:
                        logger.info(
                            "[FIRAC CACHE] Tentando parsear raw text para JSON..."
                        )
                        parsed_data = self._parse_raw_firac_to_json(raw)
                        if parsed_data and any(parsed_data.values()):
                            logger.info(
                                "[FIRAC CACHE] Raw text parseado com sucesso! Salvando JSON..."
                            )
                            self._cache_firac(
                                focus_key, parsed_data, raw
                            )
                            return {
                                "data": parsed_data,
                                "raw": raw,
                                "cached": True,
                            }
                        else:
                            logger.warning(
                                "[FIRAC CACHE] Raw text não pôde ser parseado. Regenerando..."
                            )

            except Exception as e:
                logger.warning(
                    f"Falha ao ler FIRAC cache: {e}. Regenerando..."
                )

        # Monta prompt FIRAC
        facts_block = (
            "\n".join([f"- {s}" for s in candidate_facts])
            if candidate_facts
            else "(nenhum fato candidato extraído diretamente – use apenas o resumo)"
        )

        prompt = (
            "Produza uma análise FIRAC estruturada em JSON válido UTF-8. "
            "Os campos obrigatórios são: "
            "facts (lista de strings), issue (string), rules (lista de strings), "
            "application (string), conclusion (string). "
            "Se o contexto não trouxer informações suficientes, preencha os campos "
            "com hipóteses razoáveis baseadas em casos jurídicos típicos semelhantes, "
            "sem deixar nenhum campo vazio. "
            "Se necessário, utilize exemplos genéricos, mas sempre em linguagem formal jurídica. "
            "Texto em português.\n\n"
            f"FATOS_CANDIDATOS:\n{facts_block}\n\nRESUMO:\n{summary}\n\nJSON:"
        )

        try:
            logger.info(f"[DEBUG] Prompt FIRAC enviado ao LLM:\n{prompt}")
            resp = self.llm.invoke(prompt)
            raw = resp.content.strip()
            data = json.loads(raw)
            self._cache_firac(focus_key, data, raw)
            logger.info(
                "[DEBUG] FIRAC GERADO pelo LLM/pipeline.py:\n"
                + json.dumps(data, ensure_ascii=False, indent=2)
            )
            return {
                "data": data,
                "raw": raw,
                "cached": False,
                "summary_cached": summary_cached,
                "candidate_facts": candidate_facts,
            }
        except Exception as e:
            logger.error(f"Falha FIRAC JSON: {e}")
            fallback_prompt = (
                "Gere análise FIRAC (Fatos, Questão, Regras, Aplicação, Conclusão) "
                "em seções numeradas. Português. Base no RESUMO.\n\nRESUMO:\n" + summary
            )
            try:
                resp2 = self.llm.invoke(fallback_prompt)
                raw_fb = resp2.content.strip()
                self._cache_firac(focus_key, None, raw_fb)
                return {
                    "data": None,
                    "raw": raw_fb,
                    "cached": False,
                    "summary_cached": summary_cached,
                    "candidate_facts": candidate_facts,
                }
            except Exception as e2:
                return {
                    "data": None,
                    "raw": f"Erro ao gerar FIRAC: {e2}",
                    "cached": False,
                    "summary_cached": summary_cached,
                    "candidate_facts": candidate_facts,
                }

    # ======================================================================
    # INTEGRAÇÃO COM PetitionGenerator
    # ======================================================================
    def analyze_firac(self, context: str) -> Dict[str, str]:
        """
        Mantido para compatibilidade com analysis_module, se necessário.
        """
        return self.case_analyzer.analyze_firac(result_dict=context)

    def generate_peticao_rascunho(
        self,
        dados_ui: Dict[str, Any],
        result_dict: Dict[str, str],
    ) -> str:
        """
        Recebe dados da UI + FIRAC estruturado e delega ao PetitionGenerator.
        """
        logger.info(
            "[DEBUG] FIRAC recebido pelo PetitionGenerator:\n"
            + json.dumps(result_dict, ensure_ascii=False, indent=2)
        )
        return self.petition_generator.generate_peticao_rascunho(
            dados_ui, result_dict
        )

    # ======================================================================
    # LISTAGEM / DELEÇÃO DE DOCUMENTOS DO CASO
    # ======================================================================
    def list_unique_case_documents(self) -> List[Dict[str, Any]]:
        """
        Busca metadados de todos os chunks no vector store do caso,
        mas retorna lista de documentos únicos (agregando por 'source').
        """
        logger.info(
            f"Listando documentos únicos para o caso {self.case_id} "
            f"(tenant={self.tenant_id})"
        )
        try:
            all_metadatas = self.case_store.get(
                include=["metadatas"]
            ).get("metadatas", [])
            if not all_metadatas:
                return []

            unique_documents: Dict[str, Dict[str, Any]] = {}

            for meta in all_metadatas:
                if meta is None:
                    continue
                source_name = meta.get("source") or meta.get("source_name")
                if not source_name:
                    continue
                if source_name not in unique_documents:
                    unique_documents[source_name] = {
                        "source": source_name,
                        "type": meta.get("type", "N/A"),
                        "chunk_count": 0,
                    }
                unique_documents[source_name]["chunk_count"] += 1

            return list(unique_documents.values())
        except Exception as e:
            logger.error(f"Erro ao listar documentos únicos: {e}", exc_info=True)
            return []

    def delete_document_by_filename(self, filename: str) -> bool:
        """
        Deleta do vector store do caso todos os chunks associados a um nome de arquivo.
        Usado em /processos/ui/<id_processo>/documentos/<filename> [DELETE]
        """
        if not filename:
            logger.warning(
                "Tentativa de deletar documento com nome de arquivo vazio."
            )
            return False

        logger.info(
            f"Iniciando deleção do arquivo '{filename}' do caso "
            f"{self.case_id} (tenant={self.tenant_id})"
        )
        try:
            results = self.case_store.get(
                where={"source": filename},
                include=[],
            )
            ids_to_delete = results.get("ids", [])

            if not ids_to_delete:
                logger.warning(
                    f"Nenhum documento encontrado com o nome '{filename}' "
                    "para deletar."
                )
                return True

            logger.info(
                f"Encontrados {len(ids_to_delete)} chunks para deletar "
                f"do arquivo '{filename}'."
            )
            self.case_store.delete(ids=ids_to_delete)
            self.case_store.persist()
            logger.info(
                f"Deleção de '{filename}' concluída e vector store do caso "
                "persistido."
            )
            return True
        except Exception as e:
            logger.error(
                f"Erro ao deletar documento '{filename}' do caso "
                f"{self.case_id}: {e}",
                exc_info=True,
            )
            return False

    # ======================================================================
    # INTEGRAÇÃO COM UPLOAD GENÉRICO (processar_upload_de_arquivo)
    # ======================================================================
    def _get_case_files_dir(self) -> Path:
        """
        Diretório físico onde os arquivos do caso serão salvos,
        por tenant + case_id. Ex.: ./cases/<tenant>/<case_id>/files
        """
        files_dir = self.case_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        return files_dir

    def processar_upload_de_arquivo(
        self,
        id_processo: str,
        nome_arquivo: str,
        conteudo_arquivo_bytes: bytes,
        id_cliente: Optional[str] = None,
        criado_por_id: Optional[int] = None,
        storage_backend: str = "local",
    ):
        """
        API de alto nível para ingestão de PDFs, imagens, TXT, áudio, vídeo etc.
        - salva o arquivo em disco;
        - indexa no vector store;
        - grava metadados na tabela documentos via CadastroManager.
        """
        from mimetypes import guess_type

        if self.case_id != id_processo:
            self.case_id = id_processo

        logger.info(
            f"Processando upload para o caso {id_processo}: {nome_arquivo} "
            f"(tenant={self.tenant_id})"
        )

        # 1) Salvar arquivo em disco
        files_dir = self._get_case_files_dir()
        filename_safe = nome_arquivo  # se quiser, pode usar secure_filename na camada Flask
        file_path = files_dir / filename_safe

        try:
            file_path.write_bytes(conteudo_arquivo_bytes)
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo em disco: {e}", exc_info=True)
            return {"status": "erro", "mensagem": f"Falha ao salvar arquivo: {e}"}

        # Metadados básicos
        storage_path = str(file_path.resolve())
        mime_type, _ = guess_type(nome_arquivo)
        tamanho_bytes = len(conteudo_arquivo_bytes)

        # Tipo lógico do documento (pdf, imagem, texto, audio, video, etc.)
        ext = Path(nome_arquivo).suffix.lower()
        if ext == ".pdf":
            tipo_doc = "pdf"
        elif ext in [".jpg", ".jpeg", ".png"]:
            tipo_doc = "imagem"
        elif ext == ".txt":
            tipo_doc = "texto"
        elif ext in [".mp3", ".wav"]:
            tipo_doc = "audio"
        elif ext in [".mp4", ".mov"]:
            tipo_doc = "video"
        else:
            tipo_doc = "outro"

        # Checksum opcional
        checksum_sha256 = hashlib.sha256(conteudo_arquivo_bytes).hexdigest()

        # 2) Ingestão no vector store (RAG)
        try:
            if tipo_doc == "pdf":
                self.ingestion_handler.add_pdf(
                    conteudo_arquivo_bytes, source_name=nome_arquivo
                )

            elif tipo_doc == "imagem":
                self.ingestion_handler.add_image(
                    conteudo_arquivo_bytes, source_name=nome_arquivo
                )

            elif tipo_doc == "texto":
                try:
                    text = conteudo_arquivo_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        text = conteudo_arquivo_bytes.decode("latin-1")
                    except Exception:
                        text = ""
                if not text.strip():
                    raise ValueError(
                        "Arquivo .txt vazio ou não pôde ser decodificado."
                    )
                self.ingestion_handler.add_text_direct(
                    text,
                    source_name=nome_arquivo,
                    metadata_override={"type": "text"},
                )

            elif tipo_doc == "audio":
                self.ingestion_handler.add_audio(
                    conteudo_arquivo_bytes,
                    source_name=nome_arquivo,
                    audio_format_suffix=ext,
                    openai_client=self.openai_client,
                )

            elif tipo_doc == "video":
                self.ingestion_handler.add_video(
                    conteudo_arquivo_bytes,
                    source_name=nome_arquivo,
                    video_format_suffix=ext,
                    openai_client=self.openai_client,
                )

            else:
                # Se quiser, pode permitir "outro" sem indexar, mas devolver erro é mais honesto
                return {
                    "status": "erro",
                    "mensagem": f"Extensão de arquivo não suportada para ingestão: {ext}",
                }

        except Exception as e:
            logger.error(
                f"Falha ao indexar arquivo '{nome_arquivo}' no vector store: {e}",
                exc_info=True,
            )
            return {"status": "erro", "mensagem": str(e)}

        # 3) Gravar metadados na tabela documentos
        try:
            if id_cliente is None:
                logger.warning(
                    "processar_upload_de_arquivo chamado sem id_cliente; "
                    "registro em documentos pode ficar incompleto."
                )
            if criado_por_id is None:
                logger.warning(
                    "processar_upload_de_arquivo chamado sem criado_por_id."
                )

            dados_doc = {
                "id_cliente": id_cliente,
                "id_processo": id_processo,
                "tipo": tipo_doc,          # 👈 agora inclui 'audio' e 'video'
                "titulo": nome_arquivo,
                "descricao": None,
                "arquivo_nome": nome_arquivo,
                "mime_type": mime_type,
                "tamanho_bytes": tamanho_bytes,
                "storage_backend": storage_backend,
                "storage_path": storage_path,
                "checksum_sha256": checksum_sha256,
                "criado_por_id": criado_por_id,
            }

            self.cadastro_manager.save_documento(dados_doc)

        except Exception as e:
            logger.error(
                f"Falha ao gravar metadados de '{nome_arquivo}' na tabela documentos: {e}",
                exc_info=True,
            )
            return {
                "status": "erro",
                "mensagem": f"Arquivo indexado, mas falha ao salvar metadados: {e}",
            }

        return {
            "status": "sucesso",
            "mensagem": f"Arquivo '{nome_arquivo}' processado e salvo.",
            "storage_path": storage_path,
            "mime_type": mime_type,
            "tamanho_bytes": tamanho_bytes,
        }


    # ======================================================================
    # KB DE EMENTAS: INGESTÃO / BUSCA / DELETE
    # ======================================================================
    def ingest_ementas_to_kb(
        self,
        ementa_documents: List[Dict[str, str]],
    ) -> int:
        """
        Gera embeddings para lista de documentos de ementas e salva
        na KB de ementas (Chroma).
        """
        logger.info(
            f"Iniciando ingestão de {len(ementa_documents)} documento(s) "
            "na KB de ementas."
        )
        docs_to_add = []
        for doc_data in ementa_documents:
            metadata = {
                "source": "ementa_kb_upload",
                "filename": doc_data.get("filename", "desconhecido"),
            }
            doc = Document(
                page_content=doc_data.get("content", ""),
                metadata=metadata,
            )
            docs_to_add.append(doc)

        if docs_to_add:
            try:
                self.ementas_kb_store.add_documents(docs_to_add)
                self.ementas_kb_store.persist()
                logger.info(
                    f"{len(docs_to_add)} documento(s) de ementas "
                    "adicionado(s) e KB de ementas persistida."
                )
                return len(docs_to_add)
            except Exception as e:
                logger.error(
                    f"Erro ao adicionar ou persistir ementas na KB: {e}",
                    exc_info=True,
                )
                return 0
        return 0

    def find_similar_ementas(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Busca ementas similares via retriever (não consome API da OpenAI).
        """
        logger.info(
            f"Buscando {top_k} ementas similares na KB para: "
            f"'{query_text[:50]}...'"
        )
        if not self.ementas_kb_retriever:
            logger.error("Retriever da KB de Ementas não foi inicializado.")
            return []

        self.ementas_kb_retriever.search_kwargs["k"] = top_k
        try:
            similar_docs = self.ementas_kb_retriever.get_relevant_documents(
                query_text
            )
            return similar_docs
        except Exception as e:
            logger.error(f"Erro ao buscar ementas similares: {e}")
            return []

    def find_similar_ementas_with_scores(
        self,
        query_text: str,
        top_k: int = 5,
    ):
        """
        similarity_search_with_score na KB de ementas.
        Retorna lista de tuplas (Document, score).
        """
        try:
            return self.ementas_kb_store.similarity_search_with_score(
                query_text,
                k=top_k,
            )
        except Exception as e:
            logger.error(
                f"Erro em similarity_search_with_score: {e}"
            )
            return []

    def get_indexed_ementa_filenames(self) -> List[str]:
        """
        Retorna lista de nomes de arquivos únicos indexados na KB de Ementas.
        """
        logger.info("Buscando nomes de arquivos na KB de Ementas...")
        try:
            all_metadatas = self.ementas_kb_store.get(
                include=["metadatas"]
            ).get("metadatas", [])
            if not all_metadatas:
                return []

            filenames = sorted(
                list(
                    set(
                        meta.get("filename")
                        for meta in all_metadatas
                        if meta.get("filename")
                    )
                )
            )
            logger.info(
                f"Encontrados {len(filenames)} arquivos únicos na KB de Ementas."
            )
            return filenames
        except Exception as e:
            logger.error(
                f"Erro ao obter nomes de arquivos da KB de Ementas: {e}",
                exc_info=True,
            )
            return []

    def delete_ementas_by_filename(self, filename: str) -> int:
        """
        Deleta todos os chunks de documentos de uma ementa específica
        na KB de Ementas.
        """
        if not filename:
            logger.warning(
                "Tentativa de deletar ementa com nome de arquivo vazio."
            )
            return 0

        logger.info(
            f"Iniciando deleção de todos os documentos da KB de Ementas "
            f"com o nome de arquivo: {filename}"
        )
        try:
            results = self.ementas_kb_store.get(
                where={"filename": filename},
                include=[],
            )
            ids_to_delete = results.get("ids", [])

            if not ids_to_delete:
                logger.warning(
                    f"Nenhum documento encontrado com o nome '{filename}' "
                    "para deletar."
                )
                return 0

            logger.info(
                f"Encontrados {len(ids_to_delete)} chunks para deletar "
                f"do arquivo '{filename}'."
            )
            self.ementas_kb_store._collection.delete(ids=ids_to_delete)
            self.ementas_kb_store.persist()
            logger.info(
                f"Deleção de '{filename}' concluída e KB de ementas persistida."
            )
            return len(ids_to_delete)
        except Exception as e:
            logger.error(
                f"Erro ao deletar ementas por nome de arquivo '{filename}': {e}",
                exc_info=True,
            )
            return 0

    # ======================================================================
    # KB GLOBAL (não específica de ementas)
    # ======================================================================
    def get_global_kb_filenames(self) -> List[str]:
        """
        Retorna lista de nomes de arquivos únicos que já foram
        indexados na KB Global.
        """
        logger.info("Buscando nomes de arquivos na KB Global...")
        try:
            all_metadatas = self.kb_store.get(
                include=["metadatas"]
            ).get("metadatas", [])
            if not all_metadatas:
                return []

            filenames = sorted(
                list(
                    set(
                        meta.get("filename")
                        for meta in all_metadatas
                        if meta and meta.get("filename")
                    )
                )
            )
            logger.info(
                f"Encontrados {len(filenames)} arquivos únicos na KB Global."
            )
            return filenames
        except Exception as e:
            logger.error(
                f"Erro ao obter nomes de arquivos da KB Global: {e}",
                exc_info=True,
            )
            return []

    def delete_from_global_kb_by_filename(self, filename: str) -> int:
        """
        Deleta da KB Global todos os chunks de documento associados a
        um nome de arquivo específico.
        """
        if not filename:
            logger.warning(
                "Tentativa de deletar da KB com nome de arquivo vazio."
            )
            return 0

        logger.info(
            f"Iniciando deleção da KB Global de todos os documentos com o "
            f"nome de arquivo: {filename}"
        )
        try:
            results = self.kb_store.get(
                where={"filename": filename},
                include=[],
            )
            ids_to_delete = results.get("ids", [])

            if not ids_to_delete:
                logger.warning(
                    f"Nenhum documento encontrado na KB Global com o nome "
                    f"'{filename}' para deletar."
                )
                return 0

            logger.info(
                f"Encontrados {len(ids_to_delete)} chunks para deletar "
                f"do arquivo '{filename}' da KB Global."
            )
            self.kb_store.delete(ids=ids_to_delete)
            self.kb_store.persist()
            logger.info(
                f"Deleção de '{filename}' concluída e KB Global persistida."
            )
            return len(ids_to_delete)
        except Exception as e:
            logger.error(
                f"Erro ao deletar da KB Global por nome de arquivo '{filename}': {e}",
                exc_info=True,
            )
            return 0


if __name__ == "__main__":
    logger.info(
        "Pipeline módulo executado diretamente - nenhum teste automático configurado."
    )
