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
        API de alto nível para ingestão de PDFs, imagens, TXT etc.
        Agora também:
        - salva o arquivo em disco;
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
        filename_safe = nome_arquivo  # se quiser, pode reaproveitar secure_filename no Flask
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

        # Tipo lógico do documento (pdf, imagem, texto, áudio, vídeo, etc.)
        ext = Path(nome_arquivo).suffix.lower()
        if ext == ".pdf":
            tipo_doc = "pdf"
        elif ext in [".jpg", ".jpeg", ".png"]:
            tipo_doc = "imagem"
        elif ext == ".txt":
            tipo_doc = "texto"
        elif ext in [".mp3", ".wav"]:
            tipo_doc = "audio"   # <<< ajustado para refletir áudio
        elif ext in [".mp4", ".mov"]:
            tipo_doc = "video"   # <<< ajustado para refletir vídeo
        else:
            tipo_doc = "outro"

        # Checksum opcional
        checksum_sha256 = hashlib.sha256(conteudo_arquivo_bytes).hexdigest()

        # 2) Ingestão no vector store (como já fazia antes)
        try:
            if ext == ".pdf":
                self.ingestion_handler.add_pdf(
                    conteudo_arquivo_bytes, source_name=nome_arquivo
                )

            elif ext in [".jpg", ".jpeg", ".png"]:
                self.ingestion_handler.add_image(
                    conteudo_arquivo_bytes, source_name=nome_arquivo
                )

            elif ext == ".txt":
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

            # 🔊 ÁUDIO
            elif ext in [".mp3", ".wav"]:
                if not getattr(self, "openai_client", None):
                    raise ValueError("openai_client não configurado para transcrição de áudio.")
                self.ingestion_handler.add_audio(
                    conteudo_arquivo_bytes,
                    source_name=nome_arquivo,
                    audio_format_suffix=ext,
                    openai_client=self.openai_client,
                )

            # 🎥 VÍDEO
            elif ext in [".mp4", ".mov"]:
                if not getattr(self, "openai_client", None):
                    raise ValueError("openai_client não configurado para transcrição de vídeo.")
                self.ingestion_handler.add_video(
                    conteudo_arquivo_bytes,
                    source_name=nome_arquivo,
                    video_format_suffix=ext,
                    openai_client=self.openai_client,
                )

            else:
                return {
                    "status": "erro",
                    "mensagem": f"Extensão de arquivo não suportada: {ext}",
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
                "tipo": tipo_doc,        # <<< aqui agora recebe 'audio'/'video' certinho
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
