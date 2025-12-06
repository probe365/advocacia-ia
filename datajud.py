# datajud.py
"""
Módulo para interagir com a API pública do DataJud (Conselho Nacional de Justiça - CNJ).
... (resto do docstring) ...
"""
import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__) # Garanta que o logger seja nomeado pelo módulo

try:
    DATAJUD_API_KEY = os.environ["DATAJUD_API_KEY"]
    if not DATAJUD_API_KEY: raise KeyError
except KeyError:
    logger.critical("Variável de ambiente 'DATAJUD_API_KEY' não configurada ou vazia.")
    raise ValueError("DATAJUD_API_KEY não encontrada. Configure a variável de ambiente.") from None

# Endpoints da API do DataJud para cada tribunal
# Esta lista é extensa e pode ser mantida/atualizada conforme necessário.
# Fonte: Documentação da API Pública do DataJud.
ENDPOINTS: Dict[str, str] = {
    "TST": "https://api-publica.datajud.cnj.jus.br/api_publica_tst/_search",
    "TSE": "https://api-publica.datajud.cnj.jus.br/api_publica_tse/_search",
    "STJ": "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search",
    "STM": "https://api-publica.datajud.cnj.jus.br/api_publica_stm/_search",
    "TRF1": "https://api-publica.datajud.cnj.jus.br/api_publica_trf1/_search",
    "TRF2": "https://api-publica.datajud.cnj.jus.br/api_publica_trf2/_search",
    "TRF3": "https://api-publica.datajud.cnj.jus.br/api_publica_trf3/_search",
    "TRF4": "https://api-publica.datajud.cnj.jus.br/api_publica_trf4/_search",
    "TRF5": "https://api-publica.datajud.cnj.jus.br/api_publica_trf5/_search",
    "TRF6": "https://api-publica.datajud.cnj.jus.br/api_publica_trf6/_search",
    "TJAC": "https://api-publica.datajud.cnj.jus.br/api_publica_tjac/_search",
    "TJAL": "https://api-publica.datajud.cnj.jus.br/api_publica_tjal/_search",
    "TJAM": "https://api-publica.datajud.cnj.jus.br/api_publica_tjam/_search",
    "TJAP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjap/_search",
    "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search",
    "TJCE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjce/_search",
    "TJDFT": "https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search", # Note: 'tjdft' e não 'TJDFT' na URL
    "TJES": "https://api-publica.datajud.cnj.jus.br/api_publica_tjes/_search",
    "TJGO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjgo/_search",
    "TJMA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjma/_search",
    "TJMG": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmg/_search",
    "TJMS": "https://api-publica.datajud.cnj.jus.br/api_publica_tjms/_search",
    "TJMT": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmt/_search",
    "TJPA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpa/_search",
    "TJPB": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpb/_search",
    "TJPE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search",
    "TJPI": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpi/_search",
    "TJPR": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search",
    "TJRJ": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search",
    "TJRN": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search",
    "TJRO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjro/_search",
    "TJRR": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrr/_search",
    "TJRS": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrs/_search",
    "TJSC": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsc/_search",
    "TJSE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjse/_search",
    "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
    "TJTO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjto/_search",
    "TRT1": "https://api-publica.datajud.cnj.jus.br/api_publica_trt1/_search",
    "TRT2": "https://api-publica.datajud.cnj.jus.br/api_publica_trt2/_search",
    "TRT3": "https://api-publica.datajud.cnj.jus.br/api_publica_trt3/_search",
    "TRT4": "https://api-publica.datajud.cnj.jus.br/api_publica_trt4/_search",
    "TRT5": "https://api-publica.datajud.cnj.jus.br/api_publica_trt5/_search",
    "TRT6": "https://api-publica.datajud.cnj.jus.br/api_publica_trt6/_search",
    "TRT7": "https://api-publica.datajud.cnj.jus.br/api_publica_trt7/_search",
    "TRT8": "https://api-publica.datajud.cnj.jus.br/api_publica_trt8/_search",
    "TRT9": "https://api-publica.datajud.cnj.jus.br/api_publica_trt9/_search",
    "TRT10": "https://api-publica.datajud.cnj.jus.br/api_publica_trt10/_search",
    "TRT11": "https://api-publica.datajud.cnj.jus.br/api_publica_trt11/_search",
    "TRT12": "https://api-publica.datajud.cnj.jus.br/api_publica_trt12/_search",
    "TRT13": "https://api-publica.datajud.cnj.jus.br/api_publica_trt13/_search",
    "TRT14": "https://api-publica.datajud.cnj.jus.br/api_publica_trt14/_search",
    "TRT15": "https://api-publica.datajud.cnj.jus.br/api_publica_trt15/_search",
    "TRT16": "https://api-publica.datajud.cnj.jus.br/api_publica_trt16/_search",
    "TRT17": "https://api-publica.datajud.cnj.jus.br/api_publica_trt17/_search",
    "TRT18": "https://api-publica.datajud.cnj.jus.br/api_publica_trt18/_search",
    "TRT19": "https://api-publica.datajud.cnj.jus.br/api_publica_trt19/_search",
    "TRT20": "https://api-publica.datajud.cnj.jus.br/api_publica_trt20/_search",
    "TRT21": "https://api-publica.datajud.cnj.jus.br/api_publica_trt21/_search",
    "TRT22": "https://api-publica.datajud.cnj.jus.br/api_publica_trt22/_search",
    "TRT23": "https://api-publica.datajud.cnj.jus.br/api_publica_trt23/_search",
    "TRT24": "https://api-publica.datajud.cnj.jus.br/api_publica_trt24/_search",
    "TRE-AC": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ac/_search",
    "TRE-AL": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-al/_search",
    "TRE-AM": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-am/_search",
    "TRE-AP": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ap/_search",
    "TRE-BA": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ba/_search",
    "TRE-CE": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ce/_search",
    "TRE-DF": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-dft/_search", # Note: 'tre-dft'
    "TRE-ES": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-es/_search",
    "TRE-GO": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-go/_search",
    "TRE-MA": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ma/_search",
    "TRE-MG": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-mg/_search",
    "TRE-MS": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ms/_search",
    "TRE-MT": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-mt/_search",
    "TRE-PA": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-pa/_search",
    "TRE-PB": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-pb/_search",
    "TRE-PE": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-pe/_search",
    "TRE-PI": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-pi/_search",
    "TRE-PR": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-pr/_search",
    "TRE-RJ": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-rj/_search",
    "TRE-RN": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-rn/_search",
    "TRE-RO": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-ro/_search",
    "TRE-RR": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-rr/_search",
    "TRE-RS": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-rs/_search",
    "TRE-SC": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-sc/_search",
    "TRE-SE": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-se/_search",
    "TRE-SP": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-sp/_search",
    "TRE-TO": "https://api-publica.datajud.cnj.jus.br/api_publica_tre-to/_search",
    "TJMMG": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmmg/_search", # Tribunal de Justiça Militar de Minas Gerais
    "TJMRS": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmrs/_search", # Tribunal de Justiça Militar do Rio Grande do Sul
    "TJMSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmsp/_search", # Tribunal de Justiça Militar de São Paulo
}


DEFAULT_REQUEST_TIMEOUT: int = 30  # Aumentei um pouco o timeout para testes

def _make_datajud_request(endpoint_url: str, query_payload: Dict[str, Any], timeout: int = DEFAULT_REQUEST_TIMEOUT) -> Dict[str, Any]:
    headers = {
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==",
        "Content-Type": "application/json",
        "User-Agent": "AdvocaciaIA/1.0 (DebugSession)" # Adicione/modifique User-Agent
    }
    logger.info(f"Realizando POST para DataJud: {endpoint_url}")
    # Para DEBUG, logar o payload completo. Em produção, pode ser verboso.
    logger.debug(f"DataJud Request Headers: {headers}") # Cuidado com a chave em logs persistentes
    logger.debug(f"DataJud Request Payload: {json.dumps(query_payload, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(endpoint_url, headers=headers, json=query_payload, timeout=timeout)
        logger.info(f"DataJud Response Status: {response.status_code}")
        # Logar uma porção significativa da resposta para análise, especialmente se houver 0 hits.
        logger.debug(f"DataJud Response Text (primeiros 1000 chars): {response.text[:1000]}")

        response.raise_for_status() 
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Erro HTTP acessando {endpoint_url}: {http_err.response.status_code}")
        logger.error(f"Corpo da resposta de erro HTTP (primeiros 1000 chars): {http_err.response.text[:1000]}") 
        raise
    except requests.exceptions.Timeout:
        logger.error(f"Timeout ({timeout}s) na requisição para {endpoint_url}")
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Erro de requisição para {endpoint_url}: {req_err}")
        raise
    except json.JSONDecodeError as json_err:
        logger.error(f"Erro ao decodificar JSON da resposta de {endpoint_url}: {json_err}")
        # `response` pode não estar definido se o erro foi antes, mas se chegou aqui, deve estar.
        if 'response' in locals() and hasattr(response, 'text'):
            logger.error(f"Resposta que causou erro JSON (primeiros 1000 chars): {response.text[:1000]}")
        raise 

def _extract_hits_from_response(response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Logar a estrutura da resposta para entender porque os hits não estão sendo encontrados
    logger.debug(f"Dados recebidos para extração de hits (chaves principais): {list(response_data.keys())}")
    if "hits" in response_data:
        hits_outer = response_data.get("hits", {})
        if isinstance(hits_outer, dict):
            logger.debug(f"Estrutura interna de 'hits': {list(hits_outer.keys())}")
            actual_hits_list = hits_outer.get("hits", [])
            if isinstance(actual_hits_list, list):
                 logger.info(f"Encontrados {len(actual_hits_list)} hits no formato padrão Elasticsearch.")
                 # Logar o primeiro hit, se houver, para ver sua estrutura
                 if actual_hits_list:
                     logger.debug(f"Primeiro hit (preview): {json.dumps(actual_hits_list[0], indent=2, ensure_ascii=False)}")
                 return [hit.get("_source", {}) for hit in actual_hits_list if isinstance(hit, dict)]
            else:
                logger.warning(f"'hits.hits' não é uma lista. Tipo: {type(actual_hits_list)}. Conteúdo (preview): {str(actual_hits_list)[:200]}")
        else:
            logger.warning(f"Campo 'hits' não é um dicionário. Tipo: {type(hits_outer)}. Conteúdo (preview): {str(hits_outer)[:200]}")
    
    legacy_list = response_data.get("listaJurisprudencia")
    if isinstance(legacy_list, list):
        logger.info(f"Encontrados {len(legacy_list)} itens no formato legado 'listaJurisprudencia'.")
        return legacy_list 

    logger.warning("Nenhum resultado encontrado nos formatos esperados na resposta da API do DataJud.")
    return []

# Em datajud.py
def fetch_datajud_jurisprudencia(
    query: str,
    tribunal: str = "STJ",
    max_results: int = 5,
    # O search_field padrão pode não ser mais 'ementa' para todos os casos.
    # Poderíamos ter uma lista de campos a serem testados ou focar em 'assuntos.nome'.
    search_fields: Optional[List[str]] = None, # Nova lista de campos
    target_subject: Optional[str] = None # Novo parâmetro para buscar por um assunto específico
) -> List[Dict[str, Any]]:
    endpoint_url = ENDPOINTS.get(tribunal.upper())
    if not endpoint_url:
        logger.error(f"Tribunal '{tribunal}' não encontrado.")
        raise ValueError(f"Tribunal '{tribunal}' não configurado.")

    logger.info(f"Buscando DataJud: T='{tribunal}', Q='{query[:50]}...', Assunto='{target_subject}', Max={max_results}, Campos='{search_fields}'")

    # Construção do payload baseada nos novos parâmetros
    query_conditions: List[Dict[str, Any]] = []

    if target_subject:
        query_conditions.append({"match": {"assuntos.nome": target_subject}})
        # Ou para busca exata no keyword, se souber o nome exato da TPU:
        # query_conditions.append({"term": {"assuntos.nome.keyword": target_subject}}) 
    
    if query and search_fields: # Se uma query de texto livre e campos foram fornecidos
        query_conditions.append({
            "simple_query_string": {
                "query": query,
                "fields": search_fields, # ex: ["ementa", "textoIntegral", "decisaoTexto"] (se existirem)
                "default_operator": "OR" # Ou AND, dependendo da necessidade
            }
        })
    elif query and not search_fields and not target_subject: # Fallback para a query original se nenhum campo/assunto especificado
         logger.warning("Nenhum search_fields ou target_subject especificado, usando query genérica em 'ementa' (pode não funcionar para todos tribunais).")
         query_conditions.append({"match": {"ementa": query}})


    if not query_conditions:
        logger.error("Nenhuma condição de query válida fornecida (nem query em campos, nem target_subject).")
        return []

    payload = {
        "query": {
            "bool": {
                "must": query_conditions # Combina todas as condições com AND
            }
        },
        "size": max_results
    }
    # Se houver apenas uma condição, pode-se usar diretamente sem o "bool" e "must"
    if len(query_conditions) == 1:
        payload["query"] = query_conditions[0]
    
    try:
        response_data = _make_datajud_request(endpoint_url, payload)
        return _extract_hits_from_response(response_data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao buscar jurisprudência para '{query}' no tribunal '{tribunal}': {e}")
        return []
    except Exception as e_unhandled:
        logger.error(f"Erro não esperado em fetch_datajud_jurisprudencia: {e_unhandled}", exc_info=True)
        return []

def fetch_datajud_por_processo(
    numero_processo: str,
    tribunal: str = "STJ",
    max_results: int = 5 # Processos geralmente têm poucos documentos associados, mas pode ser ajustado
) -> List[Dict[str, Any]]:
    """
    Busca informações de um processo específico na API do DataJud pelo seu número.

    Args:
        numero_processo (str): O número do processo a ser buscado.
                               O formato exato pode depender do tribunal e da indexação no DataJud.
        tribunal (str): A sigla do tribunal. Padrão é "STJ".
        max_results (int): Número máximo de documentos a retornar para este processo.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários (`_source`) dos documentos encontrados para o processo.
                              Retorna lista vazia se nada for encontrado ou em caso de erro.

    Raises:
        ValueError: Se a sigla do `tribunal` não estiver configurada.
        requests.exceptions.RequestException: Em caso de problemas na comunicação com a API.
    """
    endpoint_url = ENDPOINTS.get(tribunal.upper())
    if not endpoint_url:
        logger.error(f"Sigla de tribunal '{tribunal}' não encontrada nos ENDPOINTS configurados.")
        raise ValueError(f"Tribunal '{tribunal}' não configurado ou inválido.")

    logger.info(f"Buscando processo no DataJud: Tribunal='{tribunal}', Número='{numero_processo}', MaxResults={max_results}")

    payload = {
        "query": {
            # Usar "match_phrase" para busca exata do número do processo,
            # ou "term" se o campo não for analisado (text). "match" pode ser muito amplo.
            # A escolha ideal depende da análise do campo "numeroProcesso" no Elasticsearch do DataJud.
            # "match" é geralmente um bom ponto de partida.
            "match": {"numeroProcesso": numero_processo}
        },
        "size": max_results
    }

    try:
        response_data = _make_datajud_request(endpoint_url, payload)
        return _extract_hits_from_response(response_data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha ao buscar processo '{numero_processo}' no tribunal '{tribunal}': {e}")
        return []


def fetch_datajud_bool_query(
    tribunal: str,
    must_clauses: List[Dict[str, Any]],
    max_results: int = 5,
    # Adicionar outros tipos de cláusulas booleanas se necessário:
    # should_clauses: List[Dict[str, Any]] = None,
    # filter_clauses: List[Dict[str, Any]] = None,
    # must_not_clauses: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Executa uma pesquisa booleana (com cláusulas `must`) na API do DataJud.

    Args:
        tribunal (str): A sigla do tribunal.
        must_clauses (List[Dict[str, Any]]): Uma lista de dicionários, cada um representando
                                             uma cláusula `match` (ou outro tipo de query)
                                             que DEVE ser satisfeita.
                                             Ex: `[{"match": {"classe.codigo": 123}}, {"match": {"orgaoJulgador.codigo": 456}}]`
        max_results (int): Número máximo de resultados.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários (`_source`) dos documentos encontrados.
                              Retorna lista vazia se nada for encontrado ou em caso de erro.

    Raises:
        ValueError: Se a sigla do `tribunal` não estiver configurada ou `must_clauses` for vazia.
        requests.exceptions.RequestException: Em caso de problemas na comunicação com a API.
    """
    endpoint_url = ENDPOINTS.get(tribunal.upper())
    if not endpoint_url:
        logger.error(f"Sigla de tribunal '{tribunal}' não encontrada nos ENDPOINTS configurados.")
        raise ValueError(f"Tribunal '{tribunal}' não configurado ou inválido.")

    if not must_clauses:
        logger.warning("Nenhuma cláusula 'must' fornecida para a busca booleana. Retornando lista vazia.")
        return [] # Ou levantar ValueError("must_clauses não pode ser vazia.")

    logger.info(f"Executando busca booleana no DataJud: Tribunal='{tribunal}', Cláusulas='{must_clauses}', MaxResults={max_results}")

    query_structure: Dict[str, Any] = {"bool": {"must": must_clauses}}
    # Exemplo de como adicionar outras cláusulas se fossem parâmetros:
    # if should_clauses: query_structure["bool"]["should"] = should_clauses
    # if filter_clauses: query_structure["bool"]["filter"] = filter_clauses
    # if must_not_clauses: query_structure["bool"]["must_not"] = must_not_clauses

    payload = {
        "query": query_structure,
        "size": max_results
    }

    try:
        response_data = _make_datajud_request(endpoint_url, payload)
        return _extract_hits_from_response(response_data)
    except requests.exceptions.RequestException as e:
        logger.error(f"Falha na busca booleana no tribunal '{tribunal}': {e}")
        return []


if __name__ == '__main__':
    # Configuração básica de logging para o exemplo
    logging.basicConfig(
        level=logging.INFO, # Use DEBUG para ver todos os logs, INFO para menos verbosidade
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()] # Envia logs para o console
    )

    # Certifique-se de que a variável de ambiente DATAJUD_API_KEY está configurada antes de executar.
    # Exemplo: export DATAJUD_API_KEY="sua_chave_aqui" (no Linux/macOS)
    #          set DATAJUD_API_KEY="sua_chave_aqui" (no Windows Command Prompt)
    #          $Env:DATAJUD_API_KEY="sua_chave_aqui" (no Windows PowerShell)
    if "DATAJUD_API_KEY" not in os.environ or not os.environ["DATAJUD_API_KEY"]:
        print("\n[!] ATENÇÃO: A variável de ambiente DATAJUD_API_KEY não está configurada.")
        print("    Os testes de API do DataJud não serão executados.")
        print("    Configure-a com sua chave de API para prosseguir com os testes.\n")
    else:
        print(f"\n[+] Usando DATAJUD_API_KEY: ...{os.environ['DATAJUD_API_KEY'][-6:]} (últimos 6 caracteres por segurança)")

        # --- Teste fetch_datajud_jurisprudencia ---
        print("\n--- Testando fetch_datajud_jurisprudencia (STJ, ementa: 'habeas corpus') ---")
        try:
            resultados_ementa = fetch_datajud_jurisprudencia(query="habeas corpus", tribunal="STJ", max_results=2)
            if resultados_ementa:
                print(f"Encontrados {len(resultados_ementa)} resultados para 'habeas corpus':")
                for i, res in enumerate(resultados_ementa):
                    print(f"  Resultado {i+1}: Processo {res.get('numeroProcesso', 'N/A')}, Ementa (início): {res.get('ementa', '')[:100]}...")
            else:
                print("Nenhum resultado encontrado para 'habeas corpus' no STJ.")
        except Exception as e:
            print(f"Erro ao testar fetch_datajud_jurisprudencia: {e}")

        # --- Teste fetch_datajud_por_processo ---
        # Você precisará de um número de processo válido do STJ para este teste.
        # Exemplo (substitua por um número real se tiver):
        numero_processo_teste = "000012320238260000" # Formato ilustrativo, pode não existir
        print(f"\n--- Testando fetch_datajud_por_processo (STJ, processo: '{numero_processo_teste}') ---")
        try:
            resultados_processo = fetch_datajud_por_processo(numero_processo=numero_processo_teste, tribunal="STJ", max_results=1)
            if resultados_processo:
                print(f"Encontrados {len(resultados_processo)} documentos para o processo '{numero_processo_teste}':")
                for i, res in enumerate(resultados_processo):
                    print(f"  Documento {i+1}: Classe '{res.get('classe', {}).get('nome', 'N/A')}', Data Disp.: {res.get('dataDisponibilizacao', 'N/A')}")
            else:
                print(f"Nenhum documento encontrado para o processo '{numero_processo_teste}' no STJ (ou o número é inválido/não existe).")
        except Exception as e:
            print(f"Erro ao testar fetch_datajud_por_processo: {e}")

        # --- Teste fetch_datajud_bool_query ---
        # Exemplo: Buscar no TJSP por processos da classe "Procedimento Comum Cível" (código 7)
        # e que tenham "indenização por dano moral" na ementa.
        # Os códigos de classe e a estrutura exata podem variar, consulte a documentação do DataJud ou explore os dados.
        print("\n--- Testando fetch_datajud_bool_query (TJSP) ---")
        try:
            clausulas_bool = [
                {"match": {"classe.nome.keyword": "Apelação Cível"}}, # Usar .keyword para correspondência exata de strings analisadas como texto
                {"match": {"siglaTribunal": "TJSP"}}, # Filtrar pelo tribunal, se necessário dentro da query
                {"match_phrase": {"ementa": "dano moral"}} # Busca por frase exata na ementa
            ]
            # Nota: Alguns campos como 'classe.nome' podem ser do tipo 'text' e ter um subcampo '.keyword'
            # para correspondências exatas. Se a busca não funcionar como esperado, verifique o mapeamento do índice.
            
            resultados_bool = fetch_datajud_bool_query(tribunal="TJSP", must_clauses=clausulas_bool, max_results=2)
            if resultados_bool:
                print(f"Encontrados {len(resultados_bool)} resultados para a busca booleana no TJSP:")
                for i, res in enumerate(resultados_bool):
                    print(f"  Resultado {i+1}: Processo {res.get('numeroProcesso', 'N/A')}, Ementa (início): {res.get('ementa', '')[:100]}...")
            else:
                print("Nenhum resultado encontrado para a busca booleana no TJSP com os critérios fornecidos.")
        except ValueError as ve: # Captura o ValueError de tribunal inválido ou API Key
            print(f"Erro de configuração ou valor inválido: {ve}")
        except Exception as e:
            print(f"Erro ao testar fetch_datajud_bool_query: {e}")

    print("\n--- Testes do Módulo DataJud Concluídos ---")
    


# ... (resto das funções fetch_datajud_por_processo e fetch_datajud_bool_query permanecem as mesmas,
# pois elas também usam _make_datajud_request e _extract_hits_from_response) ...

# O bloco if __name__ == '__main__': pode ser usado para testes diretos deste módulo
# Certifique-se de que o logging está configurado para DEBUG nele também se for testar daqui.
