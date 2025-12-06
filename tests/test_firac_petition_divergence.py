"""
Script para avaliar divergências entre FIRAC e Petição gerada
Executa análise comparativa dos dados
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

from pipeline import Pipeline

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_firac_petition_divergence(case_id: str):
    """
    Analisa divergências entre FIRAC gerado e a Petição resultante
    """
    print("="*80)
    print(f"ANÁLISE DE DIVERGÊNCIAS FIRAC vs PETIÇÃO - Caso: {case_id}")
    print("="*80)
    
    pipeline = Pipeline(case_id=case_id)

    # 1. Gerar FIRAC
    print("\n[PASSO 1] Gerando análise FIRAC...")
    firac_raw = pipeline.generate_firac()
    firac_result: Dict[str, Any] = firac_raw or {}
    
    print(f"\n{'='*80}")
    print("RESULTADO FIRAC COMPLETO:")
    print(f"{'='*80}")
    print(f"Cached: {firac_result.get('cached', False)}")
    has_data = isinstance(firac_result.get('data'), dict)
    print(f"Has 'data': {has_data}")
    print(f"Has 'raw': {bool(firac_result.get('raw'))}")

    data_block = firac_result.get('data') if has_data else {}

    if isinstance(data_block, dict) and data_block:
        print(f"\n{'='*80}")
        print("FIRAC DATA (JSON):")
        print(f"{'='*80}")
        for key, value in data_block.items():
            print(f"\n[{key.upper()}]:")
            print(f"  Tipo: {type(value)}")
            if isinstance(value, list):
                print(f"  Quantidade de itens: {len(value)}")
                for i, item in enumerate(value[:3], 1):  # Primeiros 3 itens
                    print(f"  Item {i}: {item[:100]}..." if len(item) > 100 else f"  Item {i}: {item}")
            else:
                preview = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                print(f"  Conteúdo: {preview}")
    else:
        print("\n[AVISO] FIRAC 'data' está vazio ou None!")
        
    raw_text = str(firac_result.get('raw') or "")
    if raw_text:
        print(f"\n{'='*80}")
        print("FIRAC RAW (Text):")
        print(f"{'='*80}")
        raw_preview = raw_text[:500]
        print(raw_preview)
        print("..." if len(raw_text) > 500 else "")
    
    # 2. Preparar dados para petição
    print(f"\n{'='*80}")
    print("[PASSO 2] Preparando dados para petição...")
    print(f"{'='*80}")
    
    dados_ui = {
        'juizo': {
            'vara': '1ª',
            'especialidade': 'CÍVEL',
            'comarca': 'SÃO PAULO',
            'uf': 'SP'
        },
        'autor': {
            'nome_completo_ou_razao_social': 'AUTOR TESTE'
        },
        'reu': {
            'nome': 'RÉU TESTE'
        },
        'advogado': {
            'nome': 'Dr. Advogado Teste',
            'oab_uf': 'SP',
            'oab_numero': '123456',
            'email': 'teste@teste.com'
        },
        'outros': {
            'valor_causa_num': '10.000,00',
            'valor_causa_ext': 'dez mil reais'
        }
    }
    
    # Processar FIRAC para petição (converter listas em strings)
    data_firac = data_block if isinstance(data_block, dict) else {}
    
    print("\n[CONVERSÃO] Convertendo FIRAC para formato de petição...")
    firac_for_petition = {}
    for key in ['facts', 'issue', 'rules', 'application', 'conclusion']:
        value = data_firac.get(key, '')
        print(f"\n  {key}:")
        print(f"    Tipo original: {type(value)}")
        
        if isinstance(value, list):
            converted = '\n'.join(value)
            print(f"    Lista com {len(value)} itens convertida para string")
            print(f"    Preview: {converted[:150]}...")
        else:
            converted = str(value)
            print(f"    String mantida")
            print(f"    Preview: {converted[:150]}...")
        
        firac_for_petition[key] = converted
    
    # 3. Gerar petição
    print(f"\n{'='*80}")
    print("[PASSO 3] Gerando petição...")
    print(f"{'='*80}")
    
    try:
        peticao_txt = pipeline.generate_peticao_rascunho(dados_ui, firac_for_petition)
        
        print("\n[SUCESSO] Petição gerada!")
        print(f"Tamanho: {len(peticao_txt)} caracteres")
        
        # 4. Análise de divergências
        print(f"\n{'='*80}")
        print("ANÁLISE DE DIVERGÊNCIAS:")
        print(f"{'='*80}")
        
        # Verificar se os fatos do FIRAC aparecem na petição
        facts_original = data_firac.get('facts', '')
        if isinstance(facts_original, list):
            facts_str = ' '.join(facts_original)
        else:
            facts_str = str(facts_original)
        
        print("\n[FATOS]")
        print(f"  FIRAC: {facts_str[:200]}...")
        
        # Buscar na seção DOS FATOS da petição
        import re
        fatos_section = re.search(r'II - DOS FATOS\s*(.*?)(?=\n\s*III -|$)', peticao_txt, re.DOTALL)
        if fatos_section:
            fatos_peticao = fatos_section.group(1).strip()
            print(f"  PETIÇÃO (seção DOS FATOS): {fatos_peticao[:200]}...")
            
            # Verificar similaridade básica
            facts_words = set(facts_str.lower().split())
            petition_words = set(fatos_peticao.lower().split())
            common_words = facts_words & petition_words
            
            if len(facts_words) > 0:
                similarity = len(common_words) / len(facts_words) * 100
                print(f"  Similaridade lexical: {similarity:.1f}%")
                
                if similarity < 30:
                    print("  ⚠️  DIVERGÊNCIA ALTA! Fatos da petição muito diferentes do FIRAC")
                elif similarity < 60:
                    print("  ⚠️  DIVERGÊNCIA MÉDIA. Petição reescreveu substancialmente os fatos")
                else:
                    print("  ✓ Divergência aceitável (reescrita mantém conceitos)")
        else:
            print("  ❌ ERRO: Seção DOS FATOS não encontrada na petição!")
        
        # Verificar REGRAS/ARTIGOS
        print("\n[REGRAS/ARTIGOS]")
        rules_original = data_firac.get('rules', '')
        if isinstance(rules_original, list):
            rules_str = ' '.join(rules_original)
        else:
            rules_str = str(rules_original)
        
        print(f"  FIRAC: {rules_str[:200]}...")
        
        # Buscar artigos na petição
        artigos_petition = re.findall(r'Art\.?\s+\d+[^\n,;.]*', peticao_txt, re.IGNORECASE)
        if artigos_petition:
            print(f"  PETIÇÃO (artigos encontrados): {', '.join(artigos_petition[:5])}")
            
            # Verificar se artigos do FIRAC aparecem
            for artigo in artigos_petition[:3]:
                if artigo.lower() in rules_str.lower():
                    print(f"    ✓ {artigo} está no FIRAC")
                else:
                    print(f"    ⚠️  {artigo} NÃO está no FIRAC (pode ser adicionado pelo LLM)")
        else:
            print("  ❌ NENHUM artigo de lei encontrado na petição!")
        
        # Verificar CONCLUSÃO
        print("\n[CONCLUSÃO]")
        conclusion_original = data_firac.get('conclusion', '')
        conclusion_preview = str(conclusion_original)
        print(f"  FIRAC: {conclusion_preview[:200]}...")
        
        # A conclusão do FIRAC deve influenciar os PEDIDOS
        pedidos_section = re.search(r'V - DOS PEDIDOS\s*(.*?)(?=\n\s*VI -|$)', peticao_txt, re.DOTALL)
        if pedidos_section:
            pedidos_peticao = pedidos_section.group(1).strip()
            print(f"  PETIÇÃO (pedidos): {pedidos_peticao[:200]}...")
            
            # Verificar se há pedidos genéricos
            generic_markers = ['[DEFINIR', '[DESCREVER', '[ESPECIFICAR', 'não forneceu']
            has_generic = any(marker in pedidos_peticao for marker in generic_markers)
            
            if has_generic:
                print("  ❌ PEDIDOS GENÉRICOS detectados! Petição não usou conclusão do FIRAC")
            else:
                print("  ✓ Pedidos parecem específicos")
        
        # Salvar petição para análise
        output_file = pipeline.case_dir / "peticao_teste_divergencia.txt"
        output_file.write_text(peticao_txt, encoding='utf-8')
        print(f"\n[INFO] Petição completa salva em: {output_file}")
        
        # Resumo de problemas
        print(f"\n{'='*80}")
        print("RESUMO DE PROBLEMAS IDENTIFICADOS:")
        print(f"{'='*80}")
        
        problemas = []
        
        if not firac_result.get('data'):
            problemas.append("❌ CRÍTICO: FIRAC retornou 'data' vazio (apenas raw text)")
        
        if isinstance(data_firac.get('facts'), str) and not data_firac.get('facts'):
            problemas.append("⚠️  FATOS vazios no FIRAC")
        
        if isinstance(data_firac.get('rules'), str) and not data_firac.get('rules'):
            problemas.append("⚠️  REGRAS vazias no FIRAC")
        
        if not artigos_petition:
            problemas.append("❌ Nenhum artigo de lei na petição")
        
        if has_generic if 'has_generic' in locals() else False:
            problemas.append("❌ Pedidos genéricos (não usou conclusão do FIRAC)")
        
        if problemas:
            for p in problemas:
                print(f"  {p}")
        else:
            print("  ✓ Nenhum problema crítico detectado")
        
    except Exception as e:
        print(f"\n❌ ERRO ao gerar petição: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("FIM DA ANÁLISE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Usar um caso existente - ajuste conforme necessário
    import sys
    
    # Tentar descobrir um caso existente
    cases_dir = Path("./cases")
    if cases_dir.exists():
        existing_cases = [d.name for d in cases_dir.iterdir() if d.is_dir() and d.name.startswith('caso_')]
        if existing_cases:
            case_id = existing_cases[0]
            print(f"Usando caso existente: {case_id}")
        else:
            case_id = "caso_11b044bc"  # Caso padrão do Teobaldo
            print(f"Usando caso padrão: {case_id}")
    else:
        case_id = "caso_11b044bc"
        print(f"Usando caso padrão: {case_id}")
    
    if len(sys.argv) > 1:
        case_id = sys.argv[1]
    
    analyze_firac_petition_divergence(case_id)
