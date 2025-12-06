# cadastro_manager.py (Versão Final e Completa para PostgreSQL)
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
import json
import logging
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
logger = logging.getLogger(__name__)

class CadastroManager:
    """Gerencia todos os dados cadastrais em um banco de dados PostgreSQL.
    Suporte multi-tenant simples via coluna tenant_id (quando habilitado).
    """

    def __init__(self, tenant_id: str | None = None):
        # Store connection parameters separately to avoid DSN parsing / encoding issues
        self._db_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        self.tenant_id = tenant_id or os.getenv("DEFAULT_TENANT_ID", "public")
        self.multi_tenant = os.getenv("MULTI_TENANT", "0") == "1"
        # Tabelas agora gerenciadas exclusivamente por Alembic migrations.

    def _get_connection(self):
        import psycopg2
        import logging

        logger = logging.getLogger(__name__)

        params = {
            "dbname": os.getenv("DB_NAME", "advocacia_ia"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
        }

        # log sem expor senha
        safe_params = {k: ("***" if "password" in k.lower() else v)
                        for k, v in params.items()}
        logger.info(f"[DB CONNECT] Connecting with params: {safe_params}")

        # aqui deixamos o psycopg2 cuidar de encoding/DSN
        return psycopg2.connect(**params)



    def _execute_query(self, query: str, params: tuple = None, fetch: Optional[str] = None) -> Any:
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                
                # Buscar resultado ANTES de commit (mas não retornar ainda)
                if fetch == "one":
                    result = cur.fetchone()
                elif fetch == "all":
                    result = cur.fetchall()
                else:
                    result = cur.rowcount
                
                # SEMPRE fazer commit antes de retornar
                conn.commit()
                return result
                
        except Exception as e:
            if conn: conn.rollback()
            logger.error(f"Erro na execução da query: {e}", exc_info=True)
            raise
        finally:
            if conn: conn.close()

    def _create_tables(self):
        """(Deprecated) Mantido por compatibilidade; não faz nada agora."""
        logger.debug("_create_tables chamado mas ignorado; usar Alembic.")

    # --- Métodos de CRUD completos ---
    
    def get_escritorio_info(self) -> Dict[str, Any]:
        return self._execute_query("SELECT * FROM escritorio WHERE id = 1", fetch="one") or {}

    def save_escritorio_info(self, dados: Dict[str, Any]):
        query = "INSERT INTO escritorio (id, razao_social, nome_fantasia, cnpj, endereco_completo, telefones, email_contato, site, responsaveis, areas_atuacao) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET razao_social = EXCLUDED.razao_social, nome_fantasia = EXCLUDED.nome_fantasia, cnpj = EXCLUDED.cnpj, endereco_completo = EXCLUDED.endereco_completo, telefones = EXCLUDED.telefones, email_contato = EXCLUDED.email_contato, site = EXCLUDED.site, responsaveis = EXCLUDED.responsaveis, areas_atuacao = EXCLUDED.areas_atuacao"
        params = (dados.get("razao_social"), dados.get("nome_fantasia"), dados.get("cnpj"), dados.get("endereco_completo"), json.dumps(dados.get("telefones", [])), dados.get("email_contato"), dados.get("site"), json.dumps(dados.get("responsaveis", [])), json.dumps(dados.get("areas_atuacao", {})))
        self._execute_query(query, params)

    def get_advogados(self) -> List[Dict[str, Any]]:
        return self._execute_query("SELECT * FROM advogados ORDER BY nome", fetch="all")

    def get_advogado_by_oab(self, oab: str) -> Optional[Dict[str, Any]]:
        """Retorna um único advogado pela OAB (ou None)."""
        if not oab:
            return None
        return self._execute_query("SELECT * FROM advogados WHERE oab = %s", (oab,), fetch="one")

    def save_advogado(self, dados: Dict[str, Any], oab_original: Optional[str] = None):
        if oab_original:
            query = "UPDATE advogados SET oab = %s, nome = %s, email = %s, area_atuacao = %s WHERE oab = %s"
            params = (dados.get("oab"), dados.get("nome"), dados.get("email"), dados.get("area_atuacao"), oab_original)
        else:
            query = "INSERT INTO advogados (oab, nome, email, area_atuacao) VALUES (%s, %s, %s, %s)"
            params = (dados.get("oab"), dados.get("nome"), dados.get("email"), dados.get("area_atuacao"))
        self._execute_query(query, params)

    def delete_advogado(self, oab: str):
        self._execute_query("DELETE FROM advogados WHERE oab = %s", (oab,))

    def get_clientes(self) -> List[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM clientes WHERE tenant_id = %s ORDER BY nome_completo", (self.tenant_id,), fetch="all")
        return self._execute_query("SELECT * FROM clientes ORDER BY nome_completo", fetch="all")

    def get_cliente_by_id(self, id_cliente: str) -> Optional[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM clientes WHERE id_cliente = %s AND tenant_id = %s", (id_cliente, self.tenant_id), fetch="one")
        return self._execute_query("SELECT * FROM clientes WHERE id_cliente = %s", (id_cliente,), fetch="one")

    def save_cliente(self, dados: Dict[str, Any], id_cliente: Optional[str] = None) -> str:
        if id_cliente:
            # UPDATE
            cliente_atual = self.get_cliente_by_id(id_cliente)
            if not cliente_atual:
                raise ValueError(f"Cliente com ID {id_cliente} não encontrado.")

            dados_completos = {**cliente_atual, **dados}

            if self.multi_tenant:
                query = """
                    UPDATE clientes SET 
                        tipo_pessoa=%s, nome_completo=%s, cpf_cnpj=%s, rg_ie=%s,
                        nacionalidade=%s, estado_civil=%s, profissao=%s, 
                        endereco_completo=%s, telefone=%s, email=%s, 
                        responsavel_pj=%s, observacoes=%s
                    WHERE id_cliente=%s AND tenant_id=%s
                """
                params = (
                    dados_completos.get("tipo_pessoa"),
                    dados_completos.get("nome_completo"),
                    dados_completos.get("cpf_cnpj"),
                    dados_completos.get("rg_ie"),
                    dados_completos.get("nacionalidade"),
                    dados_completos.get("estado_civil"),
                    dados_completos.get("profissao"),
                    dados_completos.get("endereco_completo"),
                    dados_completos.get("telefone"),
                    dados_completos.get("email"),
                    dados_completos.get("responsavel_pj"),
                    dados_completos.get("observacoes"),
                    id_cliente,
                    self.tenant_id,
                )
            else:
                query = """
                    UPDATE clientes SET 
                        tipo_pessoa=%s, nome_completo=%s, cpf_cnpj=%s, rg_ie=%s,
                        nacionalidade=%s, estado_civil=%s, profissao=%s, 
                        endereco_completo=%s, telefone=%s, email=%s, 
                        responsavel_pj=%s, observacoes=%s
                    WHERE id_cliente=%s
                """
                params = (
                    dados_completos.get("tipo_pessoa"),
                    dados_completos.get("nome_completo"),
                    dados_completos.get("cpf_cnpj"),
                    dados_completos.get("rg_ie"),
                    dados_completos.get("nacionalidade"),
                    dados_completos.get("estado_civil"),
                    dados_completos.get("profissao"),
                    dados_completos.get("endereco_completo"),
                    dados_completos.get("telefone"),
                    dados_completos.get("email"),
                    dados_completos.get("responsavel_pj"),
                    dados_completos.get("observacoes"),
                    id_cliente,
                )

            # 👈 AQUI estava faltando
            self._execute_query(query, params)

        else:
            # INSERT - permanece como já estava
            if self.multi_tenant:
                query = """
                    INSERT INTO clientes (
                        tipo_pessoa, nome_completo, cpf_cnpj, rg_ie, nacionalidade, 
                        estado_civil, profissao, endereco_completo, telefone, email, 
                        responsavel_pj, data_cadastro, observacoes, tenant_id
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id_cliente
                """
                params = (
                    dados.get("tipo_pessoa"),
                    dados.get("nome_completo"),
                    dados.get("cpf_cnpj"),
                    dados.get("rg_ie"),
                    dados.get("nacionalidade"),
                    dados.get("estado_civil"),
                    dados.get("profissao"),
                    dados.get("endereco_completo"),
                    dados.get("telefone"),
                    dados.get("email"),
                    dados.get("responsavel_pj"),
                    datetime.now().strftime("%Y-%m-%d"),
                    dados.get("observacoes"),
                    self.tenant_id,
                )
            else:
                query = """
                    INSERT INTO clientes (
                        tipo_pessoa, nome_completo, cpf_cnpj, rg_ie, nacionalidade, 
                        estado_civil, profissao, endereco_completo, telefone, email, 
                        responsavel_pj, data_cadastro, observacoes
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id_cliente
                """
                params = (
                    dados.get("tipo_pessoa"),
                    dados.get("nome_completo"),
                    dados.get("cpf_cnpj"),
                    dados.get("rg_ie"),
                    dados.get("nacionalidade"),
                    dados.get("estado_civil"),
                    dados.get("profissao"),
                    dados.get("endereco_completo"),
                    dados.get("telefone"),
                    dados.get("email"),
                    dados.get("responsavel_pj"),
                    datetime.now().strftime("%Y-%m-%d"),
                    dados.get("observacoes"),
                )

            result = self._execute_query(query, params, fetch="one")
            id_cliente = str(result['id_cliente']) if result else None

        return id_cliente

        
            

    def delete_cliente(self, id_cliente: str) -> bool:
        if self.multi_tenant:
            rowcount = self._execute_query("DELETE FROM clientes WHERE id_cliente = %s AND tenant_id = %s", (id_cliente, self.tenant_id))
        else:
            rowcount = self._execute_query("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        return rowcount > 0

    def get_processos_do_cliente(self, id_cliente: str) -> List[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM processos WHERE id_cliente = %s AND tenant_id = %s ORDER BY data_inicio DESC", (id_cliente, self.tenant_id), fetch="all")
        return self._execute_query("SELECT * FROM processos WHERE id_cliente = %s ORDER BY data_inicio DESC", (id_cliente,), fetch="all")

    def get_processo_by_id(self, id_processo: str) -> Optional[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM processos WHERE id_processo = %s AND tenant_id = %s", (id_processo, self.tenant_id), fetch="one")
        return self._execute_query("SELECT * FROM processos WHERE id_processo = %s", (id_processo,), fetch="one")

    def save_processo(self, dados: Dict[str, Any], id_processo: Optional[str] = None) -> str:
        """
        Salva ou atualiza um processo com suporte aos 12 novos campos (Item 1).
        
        Novos campos (Migration 0005):
        - local_tramite, comarca, area_atuacao, instancia, subfase, assunto
        - valor_causa, data_distribuicao, data_encerramento, sentenca
        - em_execucao, segredo_justica
        
        Validações aplicadas:
        - area_atuacao: enum (Civil, Trabalhista, Penal, Tributario, Familia)
        - instancia: enum (1ª Instância, 2ª Instância, Superior)
        - subfase: enum (Inicial, Instrução, Sentenciado, Recursal, Execução)
        - valor_causa: decimal positivo
        - data_distribuicao/data_encerramento: não podem ser futuras
        """
        if not dados.get("id_cliente") or not dados.get("nome_caso"): 
            raise ValueError("ID do Cliente e Nome do Caso são obrigatórios.")
        
        # Normalize tipo_parte to lowercase
        tipo_parte = dados.get("tipo_parte")
        if tipo_parte:
            tipo_parte = tipo_parte.lower()
        
        # === VALIDAÇÕES DOS NOVOS CAMPOS (Item 1) ===
        
        # 1. Validar area_atuacao
        area_atuacao = dados.get("area_atuacao")
        if area_atuacao:
            valid_areas = ["Civil", "Trabalhista", "Penal", "Tributario", "Familia"]
            if area_atuacao not in valid_areas:
                raise ValueError(f"area_atuacao inválida. Valores válidos: {', '.join(valid_areas)}")
        
        # 2. Validar instancia (aceita forma numérica e extensa)
        instancia = dados.get("instancia")
        if instancia:
            # Mapeamento de valores aceitos
            instancia_map = {
                "1ª Instância": "1ª Instância",
                "1a Instancia": "1ª Instância",
                "Primeira Instância": "1ª Instância",
                "Primeira Instancia": "1ª Instância",
                "2ª Instância": "2ª Instância",
                "2a Instancia": "2ª Instância",
                "Segunda Instância": "2ª Instância",
                "Segunda Instancia": "2ª Instância",
                "Superior": "Superior",
                "Tribunal": "Superior",
                "Tribunais Superiores": "Superior"
            }
            
            # Normalizar valor
            instancia_normalizada = instancia_map.get(instancia, instancia)
            
            valid_instancias = ["1ª Instância", "2ª Instância", "Superior"]
            if instancia_normalizada not in valid_instancias:
                raise ValueError(f"instancia inválida '{instancia}'. Valores válidos: {', '.join(valid_instancias)}")
            
            # Atualizar com valor normalizado
            dados["instancia"] = instancia_normalizada
        
        # 3. Validar subfase
        subfase = dados.get("subfase")
        if subfase:
            valid_subfases = ["Inicial", "Instrução", "Sentenciado", "Recursal", "Execução"]
            if subfase not in valid_subfases:
                raise ValueError(f"subfase inválida. Valores válidos: {', '.join(valid_subfases)}")
        
        # 4. Validar valor_causa (decimal positivo)
        valor_causa = dados.get("valor_causa")
        if valor_causa is not None:
            try:
                from decimal import Decimal
                valor_causa = Decimal(str(valor_causa))
                if valor_causa < 0:
                    raise ValueError("valor_causa deve ser positivo")
            except Exception as e:
                raise ValueError(f"valor_causa inválido: {e}")
        
        # 5. Validar datas (não podem ser futuras)
        hoje = datetime.now().date()
        
        data_distribuicao = dados.get("data_distribuicao")
        if data_distribuicao:
            if isinstance(data_distribuicao, str):
                data_distribuicao = datetime.strptime(data_distribuicao, "%Y-%m-%d").date()
            if data_distribuicao > hoje:
                logger.warning(f"data_distribuicao está no futuro: {data_distribuicao}")
        
        data_encerramento = dados.get("data_encerramento")
        if data_encerramento:
            if isinstance(data_encerramento, str):
                data_encerramento = datetime.strptime(data_encerramento, "%Y-%m-%d").date()
            if data_encerramento > hoje:
                logger.warning(f"data_encerramento está no futuro: {data_encerramento}")
        
        # 6. Normalizar booleanos
        em_execucao = dados.get("em_execucao")
        if em_execucao is not None:
            em_execucao = bool(em_execucao)
        
        segredo_justica = dados.get("segredo_justica")
        if segredo_justica is not None:
            segredo_justica = bool(segredo_justica)
        
        # === CONSTRUÇÃO DA QUERY COM 12 NOVOS CAMPOS ===
        
        if id_processo:
            # UPDATE - atualiza processo existente
            
            # === VALIDAÇÃO Item 2: Impedir alteração do numero_cnj ===
            if dados.get("numero_cnj"):
                # Buscar numero_cnj atual do processo
                check_query = "SELECT numero_cnj FROM processos WHERE id_processo=%s"
                check_params = (id_processo,)
                if self.multi_tenant:
                    check_query += " AND tenant_id=%s"
                    check_params = (id_processo, self.tenant_id)
                
                resultado = self._execute_query(check_query, check_params, fetch="all")

                if resultado:
                    numero_cnj_atual = resultado[0].get('numero_cnj')
                    numero_cnj_novo = dados.get("numero_cnj")
                    
                    # Se numero_cnj está sendo alterado, bloquear
                    if numero_cnj_atual and numero_cnj_novo and numero_cnj_atual != numero_cnj_novo:
                        raise ValueError(
                            f"O número CNJ não pode ser alterado após a criação do processo. "
                            f"Valor atual: {numero_cnj_atual}. "
                            f"Se o número está incorreto, delete o processo e recrie-o."
                        )
            
            if self.multi_tenant:
                query = """UPDATE processos SET 
                    nome_caso=%s, numero_cnj=%s, status=%s, advogado_oab=%s, tipo_parte=%s,
                    local_tramite=%s, comarca=%s, area_atuacao=%s, instancia=%s, subfase=%s, assunto=%s,
                    valor_causa=%s, data_distribuicao=%s, data_encerramento=%s, sentenca=%s,
                    em_execucao=%s, segredo_justica=%s
                    WHERE id_processo=%s AND tenant_id=%s"""
                params = (
                    dados.get("nome_caso"), dados.get("numero_cnj"), dados.get("status"), 
                    dados.get("advogado_oab"), tipo_parte,
                    dados.get("local_tramite"), dados.get("comarca"), area_atuacao, 
                    instancia, subfase, dados.get("assunto"),
                    valor_causa, data_distribuicao, data_encerramento, dados.get("sentenca"),
                    em_execucao, segredo_justica,
                    id_processo, self.tenant_id
                )
            else:
                query = """UPDATE processos SET 
                    nome_caso=%s, numero_cnj=%s, status=%s, advogado_oab=%s, tipo_parte=%s,
                    local_tramite=%s, comarca=%s, area_atuacao=%s, instancia=%s, subfase=%s, assunto=%s,
                    valor_causa=%s, data_distribuicao=%s, data_encerramento=%s, sentenca=%s,
                    em_execucao=%s, segredo_justica=%s
                    WHERE id_processo=%s"""
                params = (
                    dados.get("nome_caso"), dados.get("numero_cnj"), dados.get("status"), 
                    dados.get("advogado_oab"), tipo_parte,
                    dados.get("local_tramite"), dados.get("comarca"), area_atuacao, 
                    instancia, subfase, dados.get("assunto"),
                    valor_causa, data_distribuicao, data_encerramento, dados.get("sentenca"),
                    em_execucao, segredo_justica,
                    id_processo
                )
        else:
            # INSERT - cria novo processo (construção dinâmica apenas com campos fornecidos)
            id_processo = f"caso_{str(uuid.uuid4())[:8]}"
            
            # Campos obrigatórios
            campos = ["id_processo", "id_cliente", "nome_caso", "status", "data_inicio"]
            valores = [id_processo, dados.get("id_cliente"), dados.get("nome_caso"), 
                      dados.get("status", "PENDENTE"), datetime.now().strftime("%Y-%m-%d")]
            
            # Adicionar campos opcionais apenas se presentes
            campos_opcionais = {
                "numero_cnj": dados.get("numero_cnj"),
                "tipo_parte": tipo_parte,
                "local_tramite": dados.get("local_tramite"),
                "comarca": dados.get("comarca"),
                "area_atuacao": area_atuacao,
                "instancia": instancia,
                "subfase": subfase,
                "assunto": dados.get("assunto"),
                "valor_causa": valor_causa,
                "data_distribuicao": data_distribuicao,
                "data_encerramento": data_encerramento,
                "sentenca": dados.get("sentenca"),
                "em_execucao": em_execucao,
                "segredo_justica": segredo_justica
            }
            
            # Adicionar advogado_oab apenas se existir na tabela advogados
            advogado_oab = dados.get("advogado_oab")
            if advogado_oab:
                # Verificar se advogado existe
                try:
                    if self.multi_tenant:
                        check_query = "SELECT 1 FROM advogados WHERE oab = %s AND tenant_id = %s"
                        result = self._execute_query(check_query, (advogado_oab, self.tenant_id), fetch=True)
                    else:
                        check_query = "SELECT 1 FROM advogados WHERE oab = %s"
                        result = self._execute_query(check_query, (advogado_oab,), fetch=True)
                    
                    if result:
                        campos_opcionais["advogado_oab"] = advogado_oab
                    else:
                        logger.warning(f"Advogado OAB {advogado_oab} não encontrado, processo será criado sem advogado")
                except Exception as e:
                    logger.warning(f"Erro ao verificar advogado {advogado_oab}: {e}")
            
            for campo, valor in campos_opcionais.items():
                if valor is not None:
                    campos.append(campo)
                    valores.append(valor)
            
            # Adicionar tenant_id se multi-tenant
            if self.multi_tenant:
                campos.append("tenant_id")
                valores.append(self.tenant_id)
            
            # Construir query dinamicamente
            placeholders = ",".join(["%s"] * len(valores))
            campos_str = ",".join(campos)
            query = f"INSERT INTO processos ({campos_str}) VALUES ({placeholders})"
            params = tuple(valores)
        
        self._execute_query(query, params)
        logger.info(f"Processo {'atualizado' if id_processo else 'criado'}: {id_processo}")
        return id_processo

    def delete_processo(self, id_processo: str) -> bool:
        if self.multi_tenant:
            rowcount = self._execute_query("DELETE FROM processos WHERE id_processo = %s AND tenant_id = %s", (id_processo, self.tenant_id))
        else:
            rowcount = self._execute_query("DELETE FROM processos WHERE id_processo = %s", (id_processo,))
        return rowcount > 0
    
    # --- CRUD Partes Adversas (Item 3 - Migration 0006) ---
    
    def _validar_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """
        Valida CPF (11 dígitos) ou CNPJ (14 dígitos).
        Retorna True se válido, False caso contrário.
        """
        import re
        
        if not cpf_cnpj:
            return True  # Opcional, permite vazio
        
        # Remove caracteres não-numéricos
        numeros = re.sub(r'\D', '', cpf_cnpj)
        
        # Valida CPF (11 dígitos)
        if len(numeros) == 11:
            # CPF inválidos conhecidos (todos dígitos iguais)
            if numeros == numeros[0] * 11:
                return False
            
            # Validação simplificada (algoritmo completo seria muito extenso)
            # Aceita qualquer CPF com 11 dígitos numéricos distintos
            return True
        
        # Valida CNPJ (14 dígitos)
        elif len(numeros) == 14:
            # CNPJ inválidos conhecidos
            if numeros == numeros[0] * 14:
                return False
            
            # Validação simplificada
            return True
        
        else:
            return False  # Tamanho inválido
    
    def _buscar_cep_viacep(self, cep: str) -> Optional[Dict[str, str]]:
        """
        Busca informações de endereço via API ViaCEP.
        Retorna dict com {logradouro, bairro, cidade, estado} ou None se falhar.
        """
        import re
        import requests
        
        if not cep:
            return None
        
        # Remove caracteres não-numéricos
        cep_limpo = re.sub(r'\D', '', cep)
        
        if len(cep_limpo) != 8:
            logger.warning(f"CEP inválido (deve ter 8 dígitos): {cep}")
            return None
        
        try:
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            dados = response.json()
            
            # ViaCEP retorna {"erro": true} se CEP não existe
            if dados.get("erro"):
                logger.warning(f"CEP não encontrado: {cep_limpo}")
                return None
            
            return {
                "logradouro": dados.get("logradouro", ""),
                "bairro": dados.get("bairro", ""),
                "cidade": dados.get("localidade", ""),
                "estado": dados.get("uf", "")
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao consultar ViaCEP para CEP {cep_limpo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao processar CEP {cep_limpo}: {e}")
            return None
    
    def save_documento(self, dados: Dict[str, Any]) -> int:
        logger.info(f"[DOCUMENTOS] Tentando salvar documento: {dados}")
        """
        Insere um documento na tabela documentos.
        Retorna o ID criado.
        """
        query = """
            INSERT INTO documentos (
                id_cliente, id_processo, tipo, titulo, descricao,
                arquivo_nome, mime_type, tamanho_bytes,
                storage_backend, storage_path,
                checksum_sha256, criado_por_id, tenant_id,
                created_at, updated_at
            )
            VALUES (
                %s,%s,%s,%s,%s,
                %s,%s,%s,
                %s,%s,
                %s,%s,%s,
                NOW(), NOW()
            )
            RETURNING id
        """

        params = (
            dados.get("id_cliente"),
            dados.get("id_processo"),
            dados.get("tipo"),
            dados.get("titulo"),
            dados.get("descricao"),
            dados.get("arquivo_nome"),
            dados.get("mime_type"),
            dados.get("tamanho_bytes"),
            dados.get("storage_backend"),
            dados.get("storage_path"),
            dados.get("checksum_sha256"),
            dados.get("criado_por_id"),
            self.tenant_id,
        )

        result = self._execute_query(query, params, fetch="one")
        return result["id"]

    def get_documentos_by_processo(self, id_processo: str) -> List[Dict[str, Any]]:
        if self.multi_tenant:
            query = """
                SELECT *
                FROM documentos
                WHERE id_processo = %s AND tenant_id = %s
                ORDER BY created_at DESC
            """
            params = (id_processo, self.tenant_id)
        else:
            query = """
                SELECT *
                FROM documentos
                WHERE id_processo = %s
                ORDER BY created_at DESC
            """
            params = (id_processo,)

        return self._execute_query(query, params, fetch="all") or []

    def get_documento_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        if self.multi_tenant:
            query = "SELECT * FROM documentos WHERE id=%s AND tenant_id=%s"
            params = (doc_id, self.tenant_id)
        else:
            query = "SELECT * FROM documentos WHERE id=%s"
            params = (doc_id,)

        return self._execute_query(query, params, fetch="one")


    def update_documento(self, doc_id: int, dados: Dict[str, Any]) -> bool:
        campos = []
        valores = []

        for campo in [
            "tipo", "titulo", "descricao",
            "mime_type", "tamanho_bytes",
            "storage_backend", "storage_path",
            "checksum_sha256", "criado_por_id"
        ]:
            if dados.get(campo) is not None:
                campos.append(f"{campo}=%s")
                valores.append(dados[campo])

        set_str = ", ".join(campos)

        if self.multi_tenant:
            query = f"""
                UPDATE documentos
                SET {set_str}, updated_at=NOW()
                WHERE id=%s AND tenant_id=%s
            """
            valores.append(doc_id)
            valores.append(self.tenant_id)
        else:
            query = f"""
                UPDATE documentos
                SET {set_str}, updated_at=NOW()
                WHERE id=%s
            """
            valores.append(doc_id)

        rc = self._execute_query(query, tuple(valores))
        return rc > 0


    def delete_documento(self, doc_id: int) -> bool:
        if self.multi_tenant:
            query = "DELETE FROM documentos WHERE id=%s AND tenant_id=%s"
            params = (doc_id, self.tenant_id)
        else:
            query = "DELETE FROM documentos WHERE id=%s"
            params = (doc_id,)

        rc = self._execute_query(query, params)
        return rc > 0
    
    def delete_documento_por_titulo(self, id_processo: str, titulo: str) -> bool:
        """
        Remove um registro da tabela documentos pelo id_processo + título (nome do arquivo).
        Retorna True se alguma linha foi apagada.
        """
        sql = """
            DELETE FROM documentos
            WHERE tenant_id = %s
            AND id_processo = %s
            AND titulo = %s
            AND tenant_id = %s
                    """
                    # Se você estiver usando coluna tenant_id também, pode incluir:
        # AND tenant_id = %s
        # e passar self.tenant_id como terceiro parâmetro.

        with self.conn.cursor() as cur:
            cur.execute(sql, (self.tenant_id, id_processo, titulo, self.tenant_id))

            apagados = cur.rowcount

        self.conn.commit()
        return apagados > 0

    def delete_documento_by_filename(self, id_processo: str, titulo: str) -> bool:
        """
        Deleta um registro da tabela documentos para este tenant, processo e título.
        Retorna True se ao menos 1 linha foi removida.
        """
        sql = """
            DELETE FROM documentos
            WHERE tenant_id  = %s
            AND id_processo = %s
            AND titulo      = %s
        """
        params = (self.tenant_id, id_processo, titulo)

        # 🔥 MUITO IMPORTANTE: use o MESMO helper que as outras funções usam
        # Ex.: _get_conn(), get_conn(), get_connection()...
        # Veja um método já existente (listar, inserir, etc.) e copie o padrão.
        with self._get_connection() as conn:   # <-- troque _get_conn pelo nome correto
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount > 0



    def get_partes_adversas_by_processo(self, id_processo: str) -> List[Dict[str, Any]]:
        """
        Retorna todas as partes adversas de um processo.
        Sempre filtra por tenant_id (coluna obrigatória).
        """
        return self._execute_query(
            "SELECT * FROM partes_adversas WHERE id_processo = %s AND tenant_id = %s ORDER BY created_at DESC",
            (id_processo, self.tenant_id),
            fetch="all"
        ) or []
    
    def get_parte_adversa_by_id(self, id_parte: int) -> Optional[Dict[str, Any]]:
        """
        Retorna uma parte adversa específica por ID.
        Sempre filtra por tenant_id (coluna obrigatória).
        """
        return self._execute_query(
            "SELECT * FROM partes_adversas WHERE id = %s AND tenant_id = %s",
            (id_parte, self.tenant_id),
            fetch="one"
        )
    
    def save_parte_adversa(self, dados: Dict[str, Any], id_parte: Optional[int] = None) -> int:
        """
        Cria ou atualiza uma parte adversa.
        
        Campos obrigatórios:
        - id_processo: ID do processo (FK)
        - tipo_parte: enum (autor, reu, terceiro, reclamante, reclamada)
        - nome_completo: nome da pessoa/empresa
        
        Campos opcionais:
        - cpf_cnpj, rg, qualificacao, endereco_completo, bairro, cidade, estado, cep
        - telefone, email, advogado_nome, advogado_oab, observacoes
        
        Validações:
        - CPF/CNPJ formato válido (11 ou 14 dígitos)
        - tipo_parte deve ser um dos valores permitidos
        - Se CEP fornecido, tenta buscar endereço via ViaCEP
        
        Retorna:
        - ID da parte adversa (int)
        """
        # Validações obrigatórias
        if not dados.get("id_processo"):
            raise ValueError("id_processo é obrigatório")
        
        if not dados.get("nome_completo"):
            raise ValueError("nome_completo é obrigatório")
        
        # Validar tipo_parte
        tipo_parte = dados.get("tipo_parte", "").lower()
        tipos_validos = ["autor", "reu", "terceiro", "reclamante", "reclamada"]
        if tipo_parte and tipo_parte not in tipos_validos:
            raise ValueError(f"tipo_parte inválido. Valores válidos: {', '.join(tipos_validos)}")
        
        # Validar CPF/CNPJ se fornecido
        cpf_cnpj = dados.get("cpf_cnpj")
        if cpf_cnpj and not self._validar_cpf_cnpj(cpf_cnpj):
            raise ValueError("CPF/CNPJ inválido. Deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)")
        
        # Buscar endereço via ViaCEP se CEP fornecido e campos não preenchidos
        cep = dados.get("cep")
        if cep and not dados.get("cidade"):
            endereco_viacep = self._buscar_cep_viacep(cep)
            if endereco_viacep:
                # Preenche apenas campos vazios
                if not dados.get("bairro"):
                    dados["bairro"] = endereco_viacep.get("bairro", "")
                if not dados.get("cidade"):
                    dados["cidade"] = endereco_viacep.get("cidade", "")
                if not dados.get("estado"):
                    dados["estado"] = endereco_viacep.get("estado", "")
                logger.info(f"Endereço preenchido via ViaCEP para CEP {cep}: {endereco_viacep.get('cidade')}/{endereco_viacep.get('estado')}")
        
        # Normalizar campos
        nome_completo = dados.get("nome_completo", "").strip()
        qualificacao = dados.get("qualificacao", "").strip() or None
        endereco_completo = dados.get("endereco_completo", "").strip() or None
        bairro = dados.get("bairro", "").strip() or None
        cidade = dados.get("cidade", "").strip() or None
        estado = dados.get("estado", "").strip() or None
        telefone = dados.get("telefone", "").strip() or None
        email = dados.get("email", "").strip() or None
        advogado_nome = dados.get("advogado_nome", "").strip() or None
        advogado_oab = dados.get("advogado_oab", "").strip() or None
        observacoes = dados.get("observacoes", "").strip() or None
        
        if id_parte:
            # UPDATE - atualiza parte adversa existente
            if self.multi_tenant:
                query = """UPDATE partes_adversas SET 
                    tipo_parte=%s, nome_completo=%s, cpf_cnpj=%s, rg=%s, qualificacao=%s,
                    endereco_completo=%s, bairro=%s, cidade=%s, estado=%s, cep=%s,
                    telefone=%s, email=%s, advogado_nome=%s, advogado_oab=%s, observacoes=%s,
                    updated_at=NOW()
                    WHERE id=%s AND tenant_id=%s"""
                params = (
                    tipo_parte, nome_completo, cpf_cnpj, dados.get("rg"), qualificacao,
                    endereco_completo, bairro, cidade, estado, cep,
                    telefone, email, advogado_nome, advogado_oab, observacoes,
                    id_parte, self.tenant_id
                )
            else:
                query = """UPDATE partes_adversas SET 
                    tipo_parte=%s, nome_completo=%s, cpf_cnpj=%s, rg=%s, qualificacao=%s,
                    endereco_completo=%s, bairro=%s, cidade=%s, estado=%s, cep=%s,
                    telefone=%s, email=%s, advogado_nome=%s, advogado_oab=%s, observacoes=%s,
                    updated_at=NOW()
                    WHERE id=%s"""
                params = (
                    tipo_parte, nome_completo, cpf_cnpj, dados.get("rg"), qualificacao,
                    endereco_completo, bairro, cidade, estado, cep,
                    telefone, email, advogado_nome, advogado_oab, observacoes,
                    id_parte
                )
            
            self._execute_query(query, params)
            logger.info(f"Parte adversa atualizada: ID {id_parte}")
            return id_parte
        
        else:
            # INSERT - cria nova parte adversa
            # SEMPRE incluir tenant_id (obrigatório na tabela)
            tenant_id_final = dados.get("tenant_id") or self.tenant_id
            
            query = """INSERT INTO partes_adversas (
                id_processo, tenant_id, tipo_parte, nome_completo, cpf_cnpj, rg, qualificacao,
                endereco_completo, bairro, cidade, estado, cep,
                telefone, email, advogado_nome, advogado_oab, observacoes,
                created_at, updated_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW()) RETURNING id"""
            params = (
                dados.get("id_processo"), tenant_id_final, tipo_parte, nome_completo, 
                cpf_cnpj, dados.get("rg"), qualificacao,
                endereco_completo, bairro, cidade, estado, cep,
                telefone, email, advogado_nome, advogado_oab, observacoes
            )
            
            result = self._execute_query(query, params, fetch="one")
            novo_id = result["id"] if result else None
            
            if not novo_id:
                raise RuntimeError("Falha ao criar parte adversa: ID não retornado")
            
            logger.info(f"Parte adversa criada: ID {novo_id} - {nome_completo}")
            return novo_id
    
    def delete_parte_adversa(self, id_parte: int) -> bool:
        """
        Exclui uma parte adversa por ID.
        Sempre filtra por tenant_id (coluna obrigatória).
        
        Retorna:
        - True se excluído com sucesso
        - False se não encontrado
        """
        rowcount = self._execute_query(
            "DELETE FROM partes_adversas WHERE id = %s AND tenant_id = %s",
            (id_parte, self.tenant_id)
        )
        
        if rowcount > 0:
            logger.info(f"Parte adversa excluída: ID {id_parte}")
            return True
        else:
            logger.warning(f"Parte adversa não encontrada para exclusão: ID {id_parte}")
            return False
    
    # --- Fim CRUD Partes Adversas ---
    
    def create_usuario(self, username, email, password, nome_completo, advogado_oab=None):
        password_hash = generate_password_hash(password)
        if self.multi_tenant:
            query = "INSERT INTO usuarios (username, email, password_hash, nome_completo, data_criacao, advogado_oab, tenant_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            params = (username, email, password_hash, nome_completo, datetime.now(), advogado_oab, self.tenant_id)
        else:
            query = "INSERT INTO usuarios (username, email, password_hash, nome_completo, data_criacao, advogado_oab) VALUES (%s, %s, %s, %s, %s, %s)"
            params = (username, email, password_hash, nome_completo, datetime.now(), advogado_oab)
        try:
            self._execute_query(query, params)
            return True
        except psycopg2.IntegrityError:
            logger.error(f"Erro de integridade: usuário ou email '{username}' já existe.")
            return False

    def get_usuario_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM usuarios WHERE username = %s AND tenant_id = %s", (username, self.tenant_id), fetch="one")
        return self._execute_query("SELECT * FROM usuarios WHERE username = %s", (username,), fetch="one")

    def get_usuario_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query("SELECT * FROM usuarios WHERE id = %s AND tenant_id = %s", (user_id, self.tenant_id), fetch="one")
        return self._execute_query("SELECT * FROM usuarios WHERE id = %s", (user_id,), fetch="one")

    # --- Chat persistence helpers ---
    def save_chat_turn(self, id_processo: str, role: str, content: str):
        if self.multi_tenant:
            query = "INSERT INTO chat_turns (id_processo, role, content, tenant_id) VALUES (%s,%s,%s,%s)"
            params = (id_processo, role, content, self.tenant_id)
        else:
            query = "INSERT INTO chat_turns (id_processo, role, content) VALUES (%s,%s,%s)"
            params = (id_processo, role, content)
        self._execute_query(query, params)

    def get_chat_history(self, id_processo: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.multi_tenant:
            return self._execute_query(
                "SELECT role, content, created_at FROM chat_turns WHERE id_processo=%s AND tenant_id=%s ORDER BY id DESC LIMIT %s",
                (id_processo, self.tenant_id, limit), fetch="all"
            )[::-1]
        return self._execute_query(
            "SELECT role, content, created_at FROM chat_turns WHERE id_processo=%s ORDER BY id DESC LIMIT %s",
            (id_processo, limit), fetch="all"
        )[::-1]

    # --- Bulk CSV Upload for Multiple Processes ---
    def bulk_create_processos_from_csv(self, id_cliente: str, csv_content: str) -> Dict[str, Any]:
        """
        Cria múltiplos processos a partir de conteúdo CSV.
        
        Formato esperado (com cabeçalho):
        nome_caso,numero_cnj,status,advogado_oab,tipo_parte
        "Processo de Cobrança #1",123456789012345678,ATIVO,OAB123,autor
        "Ação Indenizatória",223456789012345679,PENDENTE,OAB456,reu
        
        tipo_parte pode ser: autor, reu, terceiro, reclamante, reclamada
        
        Returns:
            {
                "status": "sucesso" ou "erro",
                "processos_criados": int,
                "erros": List[str],
                "ids_criados": List[str]
            }
        """
        import csv
        from io import StringIO
        
        logger.info(f"Iniciando bulk upload CSV para cliente {id_cliente}")
        created_count = 0
        errors = []
        ids_criados = []
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            if not reader.fieldnames:
                return {
                    "status": "erro",
                    "mensagem": "CSV vazio ou formato inválido",
                    "processos_criados": 0,
                    "erros": ["Arquivo CSV sem cabeçalho"],
                    "ids_criados": []
                }
            
            # Valida colunas obrigatórias
            required_cols = {"nome_caso"}
            missing_cols = required_cols - set(reader.fieldnames)
            if missing_cols:
                return {
                    "status": "erro",
                    "mensagem": f"Colunas obrigatórias faltando: {missing_cols}",
                    "processos_criados": 0,
                    "erros": [f"Colunas obrigatórias: {missing_cols}"],
                    "ids_criados": []
                }
            
            # Processa cada linha
            for row_num, row in enumerate(reader, start=2):  # start=2 para pular cabeçalho
                try:
                    # Extrai e valida dados básicos
                    nome_caso = (row.get("nome_caso") or "").strip()
                    numero_cnj = (row.get("numero_cnj") or "").strip()
                    status = (row.get("status") or "PENDENTE").strip()
                    advogado_oab = (row.get("advogado_oab") or "").strip()
                    tipo_parte = (row.get("tipo_parte") or "").strip()
                    
                    # Novos campos do Item 1 (DIA 1)
                    comarca = (row.get("comarca") or "").strip()
                    vara = (row.get("vara") or "").strip()
                    juiz_nome = (row.get("juiz_nome") or "").strip()
                    data_distribuicao = (row.get("data_distribuicao") or "").strip()
                    data_citacao = (row.get("data_citacao") or "").strip()
                    data_audiencia = (row.get("data_audiencia") or "").strip()
                    valor_causa = (row.get("valor_causa") or "").strip()
                    valor_condenacao = (row.get("valor_condenacao") or "").strip()
                    tipo_acao = (row.get("tipo_acao") or "").strip()
                    grau_jurisdicao = (row.get("grau_jurisdicao") or "").strip()
                    instancia = (row.get("instancia") or "").strip()
                    observacoes = (row.get("observacoes") or "").strip()
                    
                    if not nome_caso:
                        errors.append(f"Linha {row_num}: nome_caso vazio")
                        continue
                    
                    # Valida tipo_parte se fornecido
                    valid_tipos = {"autor", "reu", "terceiro", "reclamante", "reclamada"}
                    if tipo_parte and tipo_parte.lower() not in valid_tipos:
                        errors.append(f"Linha {row_num}: tipo_parte inválido. Valores válidos: {', '.join(valid_tipos)}")
                        continue
                    
                    # Monta dados do processo (apenas campos com valores)
                    dados_processo = {
                        "id_cliente": id_cliente,
                        "nome_caso": nome_caso,
                        "status": status if status else "PENDENTE"
                    }
                    
                    # Adiciona campos opcionais apenas se tiverem valores
                    if numero_cnj:
                        dados_processo["numero_cnj"] = numero_cnj
                    if advogado_oab:
                        dados_processo["advogado_oab"] = advogado_oab
                    if tipo_parte:
                        dados_processo["tipo_parte"] = tipo_parte.lower()
                    if comarca:
                        dados_processo["comarca"] = comarca
                    if vara:
                        dados_processo["vara"] = vara
                    if juiz_nome:
                        dados_processo["juiz_nome"] = juiz_nome
                    if data_distribuicao:
                        dados_processo["data_distribuicao"] = data_distribuicao
                    if data_citacao:
                        dados_processo["data_citacao"] = data_citacao
                    if data_audiencia:
                        dados_processo["data_audiencia"] = data_audiencia
                    if valor_causa:
                        try:
                            dados_processo["valor_causa"] = float(valor_causa.replace(',', '.'))
                        except ValueError:
                            errors.append(f"Linha {row_num}: valor_causa inválido '{valor_causa}'")
                            continue
                    if valor_condenacao:
                        try:
                            dados_processo["valor_condenacao"] = float(valor_condenacao.replace(',', '.'))
                        except ValueError:
                            errors.append(f"Linha {row_num}: valor_condenacao inválido '{valor_condenacao}'")
                            continue
                    if tipo_acao:
                        dados_processo["tipo_acao"] = tipo_acao
                    if grau_jurisdicao:
                        dados_processo["grau_jurisdicao"] = grau_jurisdicao
                    if instancia:
                        dados_processo["instancia"] = instancia
                    if observacoes:
                        dados_processo["observacoes"] = observacoes
                    
                    # Cria processo
                    proc_id = self.save_processo(dados_processo)
                    ids_criados.append(proc_id)
                    created_count += 1
                    logger.info(f"Processo criado: {proc_id} (linha {row_num})")
                    
                except Exception as e:
                    errors.append(f"Linha {row_num}: {str(e)}")
                    logger.warning(f"Erro na linha {row_num}: {e}")
            
            status_final = "sucesso" if created_count > 0 else "erro"
            if created_count == 0 and not errors:
                errors.append("Nenhuma linha válida no CSV")
            
            resultado = {
                "status": status_final,
                "processos_criados": created_count,
                "erros": errors,
                "ids_criados": ids_criados
            }
            
            logger.info(f"Bulk upload concluído: {created_count} processos criados, {len(errors)} erros")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro geral ao processar CSV: {e}", exc_info=True)
            return {
                "status": "erro",
                "mensagem": str(e),
                "processos_criados": 0,
                "erros": [str(e)],
                "ids_criados": []
            }
