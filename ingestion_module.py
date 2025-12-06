# ingestion_module.py
import logging
from pathlib import Path
from io import BytesIO
from typing import List, Dict, Any, Tuple, Optional

from PIL import Image 
import pytesseract 
import pdfplumber
import spacy
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document 
from moviepy.editor import VideoFileClip
import os # Para remoção de arquivos temporários em add_video
import tempfile
import openai

from openai import OpenAI

openai.api_key = "...seu_token..."

client = OpenAI()

# Importa as novas funções utilitárias
from utils_arq import extract_text_from_pdf_bytes, extract_text_from_txt_bytes

# Funções de fetch dos módulos externos
# If 'normative_sources.py' is in a subfolder named 'Learning' inside your current directory, use:
# from .Learning.normative_sources import fetch_senado_normas, fetch_lexml_norma_html

# If 'normative_sources.py' is in the same directory as this file, use:
# from normative_sources import fetch_senado_normas, fetch_lexml_norma_html

# Choose the correct import based on your folder structure and remove the others.
from datajud import fetch_datajud_jurisprudencia, fetch_datajud_por_processo, fetch_datajud_bool_query
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logger = logging.getLogger(__name__)

class IngestionHandler:
    def __init__(self, nlp_processor: spacy.language.Language, 
                 text_splitter: RecursiveCharacterTextSplitter, 
                 label_map: Dict[str, str], 
                 case_store: Chroma, 
                 kb_store: Chroma):
        self.nlp = nlp_processor
        self.splitter = text_splitter
        self.label_map = label_map
        self.case_store = case_store
        self.kb_store = kb_store
        # self.embeddings = embeddings # Chroma lida com embeddings se embedding_function for passada na sua criação

    def _extract_entities_from_spacy_doc(self, doc: spacy.tokens.Doc) -> Dict[str, List[str]]:
        # (Código mantido da versão anterior do pipeline.py)
        structured_entities: Dict[str, List[str]] = {
            mapped_label: [] for mapped_label in self.label_map.values()
        }
        for ent in doc.ents:
            mapped_key = self.label_map.get(ent.label_)
            if mapped_key: structured_entities[mapped_key].append(ent.text)
        return {k: v for k, v in structured_entities.items() if v}

    @staticmethod
    def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
        return extract_text_from_pdf_bytes(pdf_bytes)

    def _add_text_to_case_store(self, text: str, metadata: Dict[str, Any]):
        # (Código mantido da versão anterior do pipeline.py)
        if not text.strip(): logger.warning(f"Texto vazio para add. Metadados: {metadata}"); return
        chunks = self.splitter.split_text(text)
        if not chunks: logger.warning(f"Zero chunks. Texto: {text[:200]}..."); return
        spacy_docs = list(self.nlp.pipe(chunks, batch_size=16, disable=["parser", "lemmatizer"]))
        docs_to_add = []
        for i, chunk_text in enumerate(chunks):
            spacy_doc = spacy_docs[i]; entities = self._extract_entities_from_spacy_doc(spacy_doc)
            flat_entities = {key: "; ".join(values) for key, values in entities.items()}
            combined_metadata = {**metadata, **flat_entities}
            for key, value in combined_metadata.items():
                if isinstance(value, (list, dict)): combined_metadata[key] = str(value)
            docs_to_add.append(Document(page_content=chunk_text, metadata=combined_metadata))
        if docs_to_add: self.case_store.add_documents(docs_to_add); self.case_store.persist(); logger.info(f"{len(docs_to_add)} chunks adicionados. Fonte: {metadata.get('source')}")

    def _ingest_kb(self, kb_folder_path: str):
        # (Código mantido da versão anterior do pipeline.py)
        kb_path = Path(kb_folder_path)
        if not kb_path.is_dir(): logger.warning(f"Diretório KB '{kb_folder_path}' não encontrado."); return
        logger.info(f"Ingestão KB de: {kb_folder_path}")
        pdf_files = list(kb_path.rglob("*.pdf"))
        if not pdf_files: logger.info("Nenhum PDF na KB."); return
        all_docs_kb = []
        for pdf_file in pdf_files:
            try:
                logger.debug(f"Processando KB: {pdf_file.name}")
                text_content = self._extract_text_from_pdf_bytes(pdf_file.read_bytes())
                if text_content.strip():
                    chunks = self.splitter.split_text(text_content)
                    if chunks: all_docs_kb.extend([Document(page_content=c, metadata={"source": "kb", "path": str(pdf_file), "filename": pdf_file.name}) for c in chunks])
            except Exception as e: logger.error(f"Erro processando KB '{pdf_file.name}': {e}", exc_info=True)
        if all_docs_kb: self.kb_store.add_documents(all_docs_kb); self.kb_store.persist(); logger.info(f"KB: {len(all_docs_kb)} chunks adicionados.")
        else: logger.info("Nenhum doc novo para KB.")

    

    def add_pdf(self, pdf_bytes: bytes, source_name: str = "pdf_upload") -> str: 
        # Usa a função do utils.py
        text = extract_text_from_pdf_bytes(pdf_bytes)
        if text: self._add_text_to_case_store(text, {"source": source_name, "type": "pdf"})
        else: logger.warning(f"PDF '{source_name}' não continha texto extraível.")
        return text

    def add_image(self, img_bytes: bytes, source_name: str = "image_upload") -> str: 
        text = "";
        if img_bytes.lstrip().startswith(b"%PDF"): text = self._extract_text_from_pdf_bytes(img_bytes)
        else:
            try: text = pytesseract.image_to_string(Image.open(BytesIO(img_bytes)), lang="por+eng")
            except pytesseract.TesseractNotFoundError: logger.error("Tesseract não configurado."); raise
            except Exception as e: logger.error(f"Erro ao processar imagem '{source_name}': {e}", exc_info=True)
        if text: self._add_text_to_case_store(text, {"source": source_name, "type": "image"})
        else: logger.warning(f"Nenhum texto extraído da imagem: {source_name}")
        return text

    def add_audio(
        self,
        audio_bytes: bytes,
        source_name: str = "audio_upload",
        audio_format_suffix: str = ".mp3",
        openai_client: Optional[OpenAI] = None,
    ) -> str: 
        logger.info(f"Processando áudio: {source_name}, sufixo para temp: {audio_format_suffix}")
        text = ""; tmp_path = None
        if not openai_client:
            logger.error("Cliente OpenAI não fornecido para add_audio.")
            raise ValueError("Cliente OpenAI é necessário para transcrição de áudio.")
        try:
            with tempfile.NamedTemporaryFile(suffix=audio_format_suffix, delete=False) as tmp_f:
                tmp_f.write(audio_bytes); tmp_path = tmp_f.name
            with open(tmp_path, "rb") as f_handle:
                resp = openai_client.audio.transcriptions.create(model="whisper-1", file=f_handle)
            text = resp.text if resp else ""
        except openai.APIError as e: logger.error(f"Erro API OpenAI (áudio '{source_name}'): {e}", exc_info=True); raise 
        except Exception as e: logger.error(f"Erro processando áudio '{source_name}': {e}", exc_info=True); raise
        finally:
            if tmp_path and os.path.exists(tmp_path): 
                try: os.remove(tmp_path)
                except Exception as e_rm: logger.warning(f"Falha ao remover tmp áudio {tmp_path}: {e_rm}")
        if text: self._add_text_to_case_store(text, {"source": source_name, "type": "audio"})
        else: logger.warning(f"Nenhum texto transcrito do áudio: {source_name}")
        return text

    def add_video(
        self,
        video_bytes: bytes,
        source_name: str = "video_upload",
        video_format_suffix: str = ".mp4",
        openai_client: Optional[OpenAI] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Processando vídeo: {source_name}")
        transcript = ""; audio_bytes_ext = None; tmp_vid, tmp_aud = None, None; clip = None
        if not openai_client:
            logger.error("Cliente OpenAI não fornecido para add_video (necessário para add_audio).")
            raise ValueError("Cliente OpenAI é necessário para transcrição de áudio de vídeo.")
        try:
            with tempfile.NamedTemporaryFile(suffix=video_format_suffix, delete=False) as tmp_f: tmp_f.write(video_bytes); tmp_vid = tmp_f.name
            clip = VideoFileClip(tmp_vid)
            if clip.audio:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_a_f: tmp_aud = tmp_a_f.name
                clip.audio.write_audiofile(tmp_aud, codec="pcm_s16le", logger=None) 
                with open(tmp_aud, "rb") as f_a: audio_bytes_ext = f_a.read()
                if audio_bytes_ext: transcript = self.add_audio(audio_bytes_ext, source_name=f"{source_name}_audio_extrato", audio_format_suffix=".wav", openai_client=openai_client)
            else: logger.warning(f"Vídeo '{source_name}' não contém trilha de áudio.")
        except Exception as e: logger.error(f"Erro ao processar vídeo '{source_name}': {e}", exc_info=True); raise
        finally:
            if clip:
                try:
                    clip.close()
                except:
                    pass
            if tmp_vid and os.path.exists(tmp_vid):
                try:
                    os.remove(tmp_vid)
                except Exception as e_rm:
                    logger.warning(f"Falha rm tmp vídeo: {e_rm}")
            if tmp_aud and os.path.exists(tmp_aud):
                try:
                    os.remove(tmp_aud)
                except Exception as e_rm:
                    logger.warning(f"Falha rm tmp áudio extraído: {e_rm}")
        return {"transcript": transcript, "audio_bytes": audio_bytes_ext}

    def add_text_direct(self, text: str, source_name: str = "text_input", metadata_override: Optional[Dict] = None) -> List[Tuple[str, str]]:
        # Renomeado de add_text para add_text_direct para evitar conflito com o add_text da classe Pipeline original
        if not text.strip(): logger.warning("Texto vazio para adicionar."); return []
        logger.info(f"Adicionando Texto Direto: {source_name}")
        doc_nlp = self.nlp(text); entities = self._extract_entities_from_spacy_doc(doc_nlp)
        ner_tuples = [(t,lbl) for lbl, txt_list in entities.items() for t in txt_list]
        flat_meta = {k: "; ".join(v) for k,v in entities.items()}
        final_meta = {"source": source_name, "type": "text", **flat_meta}
        if metadata_override: final_meta.update(metadata_override)
        self._add_text_to_case_store(text, final_meta)
        return ner_tuples

    def add_normas_senado(self, sigla: str, numero: Optional[int] = None, ano: Optional[int] = None) -> str:
        logger.warning("add_normas_senado desabilitado (fetch_senado_normas ausente).")
        return ""

    def add_normas_lexml(self, urn: str) -> str:
        logger.warning("add_normas_lexml desabilitado (fetch_lexml_norma_html ausente).")
        return ""

    def add_datajud_jurisprudencia(
        self,
        query: str,
        tribunal: str = "STJ",
        max_results: int = 5,
        search_field: str = "ementa",
    ) -> List[str]:
        logger.info(f"Adicionando DataJud juris: q='{query}', t='{tribunal}', f='{search_field}'")
        try:
            fields = [search_field] if search_field else None
            docs = fetch_datajud_jurisprudencia(
                query,
                tribunal,
                max_results,
                search_fields=fields,
            )
            added = []
            for d in docs:
                txt = f"Ementa:\n{d.get('ementa', '')}\n\nTexto Integral:\n{d.get('textoIntegral', '')}".strip()
                if txt: self._add_text_to_case_store(txt, {"source": "datajud_jurisprudencia", "type": "jurisprudencia", "tribunal": tribunal, "query_original": query, "numeroProcesso": d.get("numeroProcesso", "N/A")}); added.append(txt)
            return added
        except Exception as e: logger.error(f"Erro DataJud juris: {e}", exc_info=True); return []

    def add_datajud_processo(self, numero_processo: str, tribunal: str = "STJ") -> List[str]:
        logger.info(f"Adicionando DataJud proc: {numero_processo} ({tribunal})")
        try:
            docs = fetch_datajud_por_processo(numero_processo, tribunal=tribunal)
            added = []
            for d in docs:
                txt = f"Ementa:\n{d.get('ementa', '')}\n\nTexto Integral:\n{d.get('textoIntegral', '')}".strip()
                if txt: self._add_text_to_case_store(txt, {"source": "datajud_processo", "type": "jurisprudencia", "numeroProcesso": numero_processo, "tribunal": tribunal, "classe": d.get("classe", {}).get("nome", "N/A")}); added.append(txt)
            return added
        except Exception as e: logger.error(f"Erro DataJud proc: {e}", exc_info=True); return []
            
    def add_datajud_by_class_orgao(self, tribunal: str, classe_codigo: int, orgao_codigo: int, max_results: int = 5) -> List[str]:
        logger.info(f"Adicionando DataJud: t='{tribunal}', cl='{classe_codigo}', org='{orgao_codigo}'")
        try:
            must = [{"match": {"classe.codigo": classe_codigo}}, {"match": {"orgaoJulgador.codigo": orgao_codigo}}]
            docs = fetch_datajud_bool_query(tribunal, must, max_results)
            added = []
            for d in docs:
                txt = f"Ementa:\n{d.get('ementa', '')}\n\nTexto Integral:\n{d.get('textoIntegral', '')}".strip()
                if txt: self._add_text_to_case_store(txt, {"source": "datajud_class_orgao", "type": "jurisprudencia", "tribunal": tribunal, "classe_codigo": str(classe_codigo), "orgao_codigo": str(orgao_codigo), "numeroProcesso": d.get("numeroProcesso", "N/A")}); added.append(txt)
            return added
        except Exception as e: logger.error(f"Erro DataJud classe/órgão: {e}", exc_info=True); return []

