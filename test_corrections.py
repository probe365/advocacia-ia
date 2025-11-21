"""
Script simplificado para testar as correções do FIRAC
"""
import logging
from pipeline import Pipeline
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_firac_corrections():
    """Testa se FIRAC agora gera JSON válido"""
    
    # Encontrar um caso existente
    cases_dir = Path("./cases")
    existing_cases = [d.name for d in cases_dir.iterdir() if d.is_dir() and d.name.startswith('caso_')]
    
    if not existing_cases:
        print("❌ Nenhum caso encontrado em ./cases/")
        return
    
    case_id = existing_cases[0]
    print(f"\n{'='*80}")
    print(f"TESTANDO CORREÇÕES - Caso: {case_id}")
    print(f"{'='*80}\n")
    
    try:
        # Criar pipeline
        print("1. Criando Pipeline...")
        pipeline = Pipeline(case_id=case_id)
        print("   ✓ Pipeline criado\n")
        
        # Gerar FIRAC
        print("2. Gerando FIRAC...")
        firac_result = pipeline.generate_firac()
        print(f"   ✓ FIRAC gerado\n")
        
        # Verificar resultado
        print("3. Verificando resultado:")
        print(f"   - Cached: {firac_result.get('cached', False)}")
        print(f"   - Has 'data': {firac_result.get('data') is not None}")
        print(f"   - Has 'raw': {bool(firac_result.get('raw'))}")
        
        data = firac_result.get('data')
        
        if not data:
            print("\n   ❌ PROBLEMA: 'data' está vazio!")
            print(f"   Raw text preview: {firac_result.get('raw', '')[:200]}...")
            return False
        
        print("\n4. Validando campos do FIRAC:")
        fields_ok = 0
        for field in ['facts', 'issue', 'rules', 'application', 'conclusion']:
            value = data.get(field, '')
            has_content = bool(value and str(value).strip())
            status = "✓" if has_content else "❌"
            print(f"   {status} {field}: {len(str(value))} chars")
            if has_content:
                fields_ok += 1
        
        print(f"\n5. Resultado: {fields_ok}/5 campos preenchidos")
        
        if fields_ok >= 3:
            print("\n✅ CORREÇÕES BEM-SUCEDIDAS!")
            print("   FIRAC está gerando dados estruturados corretamente")
            return True
        else:
            print("\n⚠️  PARCIALMENTE CORRIGIDO")
            print("   Alguns campos ainda estão vazios")
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_firac_corrections()
    exit(0 if success else 1)
