# tools.py
import logging
import requests
from bs4 import BeautifulSoup
import arxiv
from langchain_core.tools import tool
from typing import List, Dict

logger = logging.getLogger(__name__)

@tool
def search_arxiv_papers(query: str, max_results: int = 3) -> List[Dict]:
    """
    Busca artigos científicos no site arXiv sobre um determinado tópico.
    Use esta ferramenta quando precisar encontrar pesquisas acadêmicas, artigos técnicos ou embasamento científico.
    Retorna uma lista de dicionários, cada um contendo o título, autores, link e resumo de um artigo.
    """
    try:
        logger.info(f"Executando ferramenta 'search_arxiv_papers' com a query: '{query}'")
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = list(client.results(search))
        if not results:
            return [{"info": "Nenhum artigo encontrado para esta busca."}]
        
        # Formata os resultados de forma estruturada
        formatted_results = []
        for res in results:
            formatted_results.append({
                "title": res.title,
                "authors": [author.name for author in res.authors],
                "link": res.entry_id,
                "summary": res.summary
            })
        return formatted_results
    except Exception as e:
        logger.error(f"Erro na ferramenta 'search_arxiv_papers': {e}")
        return [{"error": f"Ocorreu um erro ao tentar buscar no arXiv: {e}"}]

@tool
def fetch_web_content(url: str) -> str:
    """
    Acessa uma URL da web e extrai seu conteúdo de texto principal, limpando o HTML.
    Use esta ferramenta para obter informações de notícias, blogs, sites institucionais ou qualquer outra página da web.
    A URL fornecida deve ser válida e começar com 'http://' ou 'https://'.
    """
    try:
        logger.info(f"Executando ferramenta 'fetch_web_content' na URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Lança um erro para status ruins (4xx ou 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove tags de script, style, nav, footer, etc., para focar no conteúdo principal
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Limita o tamanho do retorno para não sobrecarregar o contexto do LLM
        return text[:4000]
    except Exception as e:
        logger.error(f"Erro na ferramenta 'fetch_web_content' com a URL {url}: {e}")
        return f"Ocorreu um erro ao tentar acessar a URL: {e}"
    