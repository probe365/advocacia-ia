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

# Optional: moviepy for video processing (requires FFmpeg)
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("moviepy not available - video processing disabled. Install FFmpeg to enable.")

import os # Para remoção de arquivos temporários em add_video
import tempfile
import openai

# Importa as novas funções utilitárias
from utils_arq import extract_text_from_pdf_bytes

# Funções de fetch dos módulos externos
# from Learning.normative_sources import fetch_senado_normas, fetch_lexml_norma_html
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
        structured_entities = {mapped_label: [] for mapped_label in self.label_map.values()}
        for ent in doc.ents:
            mapped_key = self.label_map.get(ent.label_)
            if mapped_key: structured_entities[mapped_key].append(ent.text)
        return {k: v for k, v in structured_entities.items() if v}

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
        text = ""
        try:
            if img_bytes.lstrip().startswith(b"%PDF"):
                # Caso raro: usuário enviou PDF com extensão de imagem
                text = extract_text_from_pdf_bytes(img_bytes)
            else:
                # Guardas de tamanho para evitar congelar: limitar a ~5MB e redimensionar se > 2500px
                size_mb = len(img_bytes) / (1024*1024)
                if size_mb > 8:
                    logger.warning(f"Imagem '{source_name}' muito grande ({size_mb:.1f}MB); reduzindo processamento.")
                img = Image.open(BytesIO(img_bytes))
                # Converte para RGB e escala de cinza para melhorar OCR
                if img.mode not in ("L", "RGB"):
                    img = img.convert("RGB")
                gray = img.convert("L")
                max_dim = 2500
                if max(img.size) > max_dim:
                    scale = max_dim / float(max(img.size))
                    new_size = (int(img.size[0]*scale), int(img.size[1]*scale))
                    gray = gray.resize(new_size)
                # Config PSM 6 (blocos de texto) para acelerar
                text = pytesseract.image_to_string(gray, lang="por+eng", config="--oem 3 --psm 6")
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract não configurado. Usando placeholder sem OCR.")
            text = ""
        except Exception as e:
            logger.error(f"Erro ao processar imagem '{source_name}': {e}", exc_info=True)
            text = ""
        if text and text.strip():
            self._add_text_to_case_store(text, {"source": source_name, "type": "image"})
        else:
            # Garante cadastro de metadados para listagem mesmo sem OCR
            logger.warning(f"Nenhum texto extraído da imagem: {source_name}; adicionando placeholder.")
            placeholder = "[imagem_sem_texto]"
            self._add_text_to_case_store(placeholder, {"source": source_name, "type": "image", "ocr":"none"})
        return text

    # ================= Métodos para KB Global =================
    def _add_text_to_kb_store(self, text: str, metadata: Dict[str, Any]):
        if not text or not text.strip():
            logger.warning(f"Texto KB vazio para add. Fonte={metadata.get('source')}")
            return
        
        # Validação extra: garantir que text é string
        if not isinstance(text, str):
            logger.error(f"_add_text_to_kb_store recebeu tipo inválido: {type(text)}. Convertendo para string.")
            text = str(text)
        
        # CRÍTICO: Validar e limpar encoding ANTES de adicionar ao Chroma
        # Detectar escape sequences literais (ex: \xc3\xa9) ou caracteres corrompidos (Ã©)
        if '\\x' in text[:500] or any(bad in text[:500] for bad in ['Ã©', 'Ã§', 'Ã£', 'Ãµ']):
            logger.warning(f"Detectado encoding incorreto em '{metadata.get('source')}'. Aplicando correção...")
            try:
                # Se tem escape sequences literais como string
                if '\\x' in text[:500]:
                    # Converter: "\\xc3\\xa9" -> bytes -> UTF-8 string
                    text = text.encode('latin1').decode('unicode_escape').encode('latin1').decode('utf-8')
                    logger.info(f"Corrigido escape sequences literais para '{metadata.get('source')}'")
                # Se tem caracteres corrompidos tipo "Ã©"
                elif any(bad in text[:500] for bad in ['Ã©', 'Ã§', 'Ã£']):
                    text = text.encode('latin1').decode('utf-8')
                    logger.info(f"Corrigido caracteres corrompidos para '{metadata.get('source')}'")
            except Exception as e:
                logger.error(f"Falha ao corrigir encoding: {e}. Salvando como está.")
        
        chunks = self.splitter.split_text(text)
        docs_to_add = [Document(page_content=c, metadata=metadata) for c in chunks]
        if docs_to_add:
            self.kb_store.add_documents(docs_to_add)
            self.kb_store.persist()
            logger.info(f"{len(docs_to_add)} chunks adicionados à KB. Fonte: {metadata.get('source')}")

    def add_text_kb(self, text_bytes: bytes, source_name: str = "text_kb") -> str:
        """Adiciona arquivo TXT à KB Global (mesma lógica do upload de processos)."""
        try:
            # Usar EXATAMENTE a mesma lógica que funciona em processar_upload_de_arquivo
            if isinstance(text_bytes, str):
                text = text_bytes
            else:
                try:
                    text = text_bytes.decode('utf-8')
                    logger.info(f"TXT KB '{source_name}' decodificado com UTF-8")
                except UnicodeDecodeError:
                    try:
                        text = text_bytes.decode('latin-1')
                        logger.info(f"TXT KB '{source_name}' decodificado com latin-1")
                    except Exception as e:
                        logger.error(f"Falha ao decodificar '{source_name}': {e}")
                        text = ''
            
            if not text or not text.strip():
                logger.warning(f"TXT KB '{source_name}' está vazio ou não pôde ser decodificado.")
                return text
            
            # Preview para debug
            preview = text[:150].replace('\n', ' ')
            logger.info(f"TXT KB '{source_name}' → Preview: {preview}")
            
            self._add_text_to_kb_store(text, {
                "source": source_name, 
                "filename": source_name, 
                "type": "text", 
                "scope": "kb"
            })
            
            logger.info(f"TXT KB '{source_name}' indexado ({len(text)} chars, {text.count(chr(10))} linhas)")
            return text
        except Exception as e:
            logger.error(f"Erro ao processar TXT KB '{source_name}': {e}", exc_info=True)
            return ""

    def add_pdf_kb(self, pdf_bytes: bytes, source_name: str = "pdf_kb") -> str:
        text = extract_text_from_pdf_bytes(pdf_bytes)
        if text:
            self._add_text_to_kb_store(text, {"source": source_name, "filename": source_name, "type": "pdf", "scope": "kb"})
        else:
            logger.warning(f"PDF KB '{source_name}' sem texto.")
        return text

    def add_image_kb(self, img_bytes: bytes, source_name: str = "image_kb") -> str:
        text = ""
        try:
            img = Image.open(BytesIO(img_bytes))
            if img.mode not in ("L","RGB"):
                img = img.convert("RGB")
            gray = img.convert("L")
            text = pytesseract.image_to_string(gray, lang="por+eng", config="--oem 3 --psm 6")
        except Exception as e:
            logger.error(f"Erro OCR KB imagem '{source_name}': {e}")
        if text and text.strip():
            self._add_text_to_kb_store(text, {"source": source_name, "filename": source_name, "type": "image", "scope": "kb"})
        else:
            placeholder = "[imagem_sem_texto]"
            self._add_text_to_kb_store(placeholder, {"source": source_name, "filename": source_name, "type": "image", "ocr":"none", "scope": "kb"})
        return text

    def add_audio_kb(self, audio_bytes: bytes, source_name: str = "audio_kb", audio_format_suffix: str = ".mp3", openai_client: openai.OpenAI = None) -> str:
        if not openai_client:
            logger.error("Cliente OpenAI necessário para áudio KB.")
            return ""
        tmp_path = None; text = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=audio_format_suffix, delete=False) as tmp_f:
                tmp_f.write(audio_bytes); tmp_path = tmp_f.name
            with open(tmp_path, 'rb') as f_h:
                resp = openai_client.audio.transcriptions.create(model="whisper-1", file=f_h)
            text = resp.text if resp else ""
        except Exception as e:
            logger.error(f"Erro áudio KB '{source_name}': {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
        if text:
            self._add_text_to_kb_store(text, {"source": source_name, "filename": source_name, "type": "audio", "scope": "kb"})
        return text

    def add_video_kb(self, video_bytes: bytes, source_name: str = "video_kb", video_format_suffix: str = ".mp4", openai_client: openai.OpenAI = None) -> Dict[str, Any]:
        if not MOVIEPY_AVAILABLE:
            logger.error("Video processing disabled - moviepy/FFmpeg not installed.")
            return {"transcript": ""}
        if not openai_client:
            logger.error("Cliente OpenAI necessário para vídeo KB.")
            return {"transcript":""}
        transcript = ""; tmp_vid = None; clip=None; tmp_aud=None
        try:
            with tempfile.NamedTemporaryFile(suffix=video_format_suffix, delete=False) as tmp_f: tmp_f.write(video_bytes); tmp_vid = tmp_f.name
            clip = VideoFileClip(tmp_vid)
            if clip.audio:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_a_f: tmp_aud = tmp_a_f.name
                clip.audio.write_audiofile(tmp_aud, codec="pcm_s16le", logger=None)
                with open(tmp_aud,'rb') as f_a:
                    resp = openai_client.audio.transcriptions.create(model="whisper-1", file=f_a)
                transcript = resp.text if resp else ""
        except Exception as e:
            logger.error(f"Erro vídeo KB '{source_name}': {e}")
        finally:
            if clip:
                try: clip.close()
                except: pass
            for p in [tmp_vid, tmp_aud]:
                if p and os.path.exists(p):
                    try: os.remove(p)
                    except: pass
        if transcript:
            self._add_text_to_kb_store(transcript, {"source": source_name, "filename": source_name, "type": "video", "scope": "kb"})
        return {"transcript": transcript}

    def add_text_kb(self, text: str, source_name: str = "text_kb"):
        if not text or not text.strip():
            return
        self._add_text_to_kb_store(text, {
            "source": source_name,
            "filename": source_name,
            "type": "text",
            "scope": "kb"
        })

    def add_audio(self, audio_bytes: bytes, source_name: str = "audio_upload", audio_format_suffix: str = ".mp3", openai_client: openai.OpenAI = None) -> str: 
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

    def add_video(self, video_bytes: bytes, source_name: str = "video_upload", video_format_suffix: str = ".mp4", openai_client: openai.OpenAI = None) -> Dict[str, Any]:
        logger.info(f"Processando vídeo: {source_name}")
        if not MOVIEPY_AVAILABLE:
            logger.error("Video processing disabled - moviepy/FFmpeg not installed.")
            raise ValueError("moviepy not available - install FFmpeg to enable video processing")
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

    def add_datajud_jurisprudencia(self, query: str, tribunal: str = "STJ", max_results: int = 5, search_field: str = "ementa") -> List[str]:
        logger.info(f"Adicionando DataJud juris: q='{query}', t='{tribunal}', f='{search_field}'")
        try:
            docs = fetch_datajud_jurisprudencia(query, tribunal, max_results, search_field=search_field)
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

