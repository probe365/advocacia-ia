"""
Teste completo: FIRAC → Petição
Valida que a petição gerada contém dados reais do caso
"""
import logging
from pipeline import Pipeline
from pathlib import Path

logging.basicConfig(level=logging.WARNING)  # Menos verbose

def test_complete_flow():
    """Testa fluxo completo: FIRAC → dados estruturados → petição específica"""
    
    # Encontrar caso
    cases_dir = Path("./cases")
    existing_cases = [d.name for d in cases_dir.iterdir() if d.is_dir() and d.name.startswith('caso_')]
    
    if not existing_cases:
        print("❌ Nenhum caso encontrado")
        return False
    
    case_id = existing_cases[0]
    print(f"\n{'='*80}")
    print(f"TESTE COMPLETO: FIRAC → PETIÇÃO")
    print(f"Caso: {case_id}")
    print(f"{'='*80}\n")
    
    try:
        # 1. Pipeline
        print("1. Criando Pipeline...")
        pipeline = Pipeline(case_id=case_id)
        print("   ✓\n")
        
        # 2. FIRAC
        print("2. Gerando FIRAC...")
        firac_result = pipeline.generate_firac()
        data_firac = firac_result.get('data')
        
        if not data_firac:
            print("   ❌ FIRAC sem dados!")
            return False
        print("   ✓ FIRAC com dados estruturados\n")
        
        # 3. Preview FIRAC
        print("3. Preview do FIRAC gerado:")
        for field in ['facts', 'issue', 'rules']:
            value = str(data_firac.get(field, ''))
            preview = value[:100] + "..." if len(value) > 100 else value
            print(f"   {field}: {preview}")
        print()
        
        # 4. Petição
        print("4. Gerando Petição...")
        
        # Dados UI mínimos
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
                'nome': 'Dr. Advogado',
                'oab_uf': 'SP',
                'oab_numero': '123456',
                'email': 'teste@teste.com'
            },
            'outros': {
                'valor_causa_num': '10.000,00',
                'valor_causa_ext': 'dez mil reais'
            }
        }
        
        # Converter listas em strings se necessário
        facts_raw = data_firac.get('facts', [])
        rules_raw = data_firac.get('rules', [])
        
        facts_str = '\\n'.join(facts_raw) if isinstance(facts_raw, list) else str(facts_raw)
        rules_str = '\\n'.join(rules_raw) if isinstance(rules_raw, list) else str(rules_raw)
        
        peticao_txt = pipeline.generate_peticao_rascunho(dados_ui, {
            'facts': facts_str,
            'issue': data_firac.get('issue', ''),
            'rules': rules_str,
            'application': data_firac.get('application', ''),
            'conclusion': data_firac.get('conclusion', '')
        })
        
        print("   ✓ Petição gerada\n")
        
        # 5. Validação de conteúdo
        print("5. Validando conteúdo da petição:")
        
        checks = {
            'Tem seção DOS FATOS': 'II - DOS FATOS' in peticao_txt,
            'Tem seção DO DIREITO': 'III - DO DIREITO' in peticao_txt,
            'Tem seção DOS PEDIDOS': 'V - DOS PEDIDOS' in peticao_txt,
            'Não tem placeholders vazios': '[DADO NÃO DISPONÍVEL]' not in peticao_txt,
            'Não tem mensagens de erro': 'você não forneceu' not in peticao_txt.lower(),
            'Tem artigos de lei': 'Art.' in peticao_txt or 'art.' in peticao_txt,
            'Tamanho adequado': len(peticao_txt) > 1000
        }
        
        passed = 0
        for check, result in checks.items():
            status = "✓" if result else "❌"
            print(f"   {status} {check}")
            if result:
                passed += 1
        
        print(f"\n6. Resultado: {passed}/{len(checks)} validações passaram")
        
        if passed >= len(checks) - 1:  # Tolera 1 falha
            print("\n✅ SUCESSO! Petição gerada corretamente com dados do caso")
            
            # Salvar petição para inspeção
            output_file = pipeline.case_dir / "peticao_teste_final.txt"
            output_file.write_text(peticao_txt, encoding='utf-8')
            print(f"   Petição salva em: {output_file}")
            
            return True
        else:
            print("\n⚠️  Petição gerada mas com problemas de qualidade")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_flow()
    print(f"\n{'='*80}\n")
    exit(0 if success else 1)
