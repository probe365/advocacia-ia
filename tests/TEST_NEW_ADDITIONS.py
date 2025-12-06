#!/usr/bin/env python3
"""
TEST_NEW_ADDITIONS.py
Comprehensive test suite for the new tipo_parte feature (Phase 1)

Tests:
1. Database connection
2. tipo_parte validation
3. Single process creation with tipo_parte
4. Bulk CSV upload with tipo_parte
5. Data verification
6. Helper functions
"""

import os
import sys
from datetime import datetime
from cadastro_manager import CadastroManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def test_1_database_connection():
    """Test 1: Database Connection"""
    print_header("TEST 1: Database Connection")
    
    try:
        manager = CadastroManager()
        info = manager.get_escritorio_info()
        print_success(f"Connected to database successfully")
        print_info(f"Escritório: {info.get('razao_social', 'N/A') if info else 'No data'}")
        return True
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False

def test_2_helper_functions():
    """Test 2: Helper Functions for tipo_parte"""
    print_header("TEST 2: Helper Functions (tipo_parte_helpers.py)")
    
    try:
        # Import helpers
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "tipo_parte_helpers",
            "app/utils/tipo_parte_helpers.py"
        )
        helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helpers)
        
        print_info("Testing helper functions...")
        
        # Test 1: validate_tipo_parte
        valid_values = ["autor", "reu", "terceiro", "reclamante", "reclamada"]
        for valor in valid_values:
            result = helpers.validate_tipo_parte(valor)
            if result:
                print_success(f"validate_tipo_parte('{valor}') = {result}")
            else:
                print_error(f"validate_tipo_parte('{valor}') failed")
                return False
        
        # Test invalid value
        result = helpers.validate_tipo_parte("invalid")
        if not result:
            print_success(f"validate_tipo_parte('invalid') correctly rejected")
        else:
            print_error(f"validate_tipo_parte('invalid') should have rejected")
            return False
        
        # Test 2: get_tipo_parte_label
        labels = {
            "autor": "Autor",
            "reu": "Réu",
            "terceiro": "Terceiro",
            "reclamante": "Reclamante",
            "reclamada": "Reclamada"
        }
        for tipo, expected_label in labels.items():
            label = helpers.get_tipo_parte_label(tipo)
            if label == expected_label:
                print_success(f"get_tipo_parte_label('{tipo}') = '{label}'")
            else:
                print_error(f"get_tipo_parte_label('{tipo}') = '{label}' (expected '{expected_label}')")
                return False
        
        # Test 3: get_tipo_parte_badge_class
        for tipo in valid_values:
            badge = helpers.get_tipo_parte_badge_class(tipo)
            if badge:
                print_success(f"get_tipo_parte_badge_class('{tipo}') = '{badge}'")
        
        # Test 4: get_tipo_parte_icon
        for tipo in valid_values:
            icon = helpers.get_tipo_parte_icon(tipo)
            if icon:
                print_success(f"get_tipo_parte_icon('{tipo}') = '{icon}'")
        
        return True
        
    except Exception as e:
        print_error(f"Helper functions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_single_processo_creation():
    """Test 3: Create Single Process with tipo_parte"""
    print_header("TEST 3: Create Single Process with tipo_parte")
    
    try:
        manager = CadastroManager()
        
        # Get real client ID
        clientes = manager.get_clientes()
        if not clientes:
            print_error("No clients found in database. Please create a client first.")
            return False
        
        id_cliente = clientes[0]['id_cliente']
        print_info(f"Using client: {clientes[0]['nome_completo']} (ID: {id_cliente})")
        
        # Get real advogado
        advogados = manager.get_advogados()
        if not advogados:
            print_error("No advogados found in database.")
            return False
        
        advogado_oab = advogados[0]['oab']
        print_info(f"Using advogado: {advogados[0]['nome']} (OAB: {advogado_oab})")
        
        # Create process with tipo_parte
        tipos_to_test = ["autor", "reu", "terceiro"]
        created_ids = []
        
        for tipo in tipos_to_test:
            dados = {
                "id_cliente": id_cliente,
                "nome_caso": f"Teste {tipo.upper()} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "numero_cnj": None,
                "status": "PENDENTE",
                "advogado_oab": advogado_oab,
                "tipo_parte": tipo
            }
            
            proc_id = manager.save_processo(dados)
            created_ids.append(proc_id)
            print_success(f"Created process with tipo_parte='{tipo}': {proc_id}")
        
        return True, created_ids
        
    except Exception as e:
        print_error(f"Single process creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_4_bulk_csv_upload():
    """Test 4: Bulk CSV Upload with tipo_parte"""
    print_header("TEST 4: Bulk CSV Upload with tipo_parte")
    
    try:
        manager = CadastroManager()
        
        # Get real client
        clientes = manager.get_clientes()
        if not clientes:
            print_error("No clients found")
            return False
        
        id_cliente = clientes[0]['id_cliente']
        
        # Get real advogados
        advogados = manager.get_advogados()
        if len(advogados) < 2:
            print_error("Need at least 2 advogados for test")
            return False
        
        oab1 = advogados[0]['oab']
        oab2 = advogados[1]['oab']
        
        # Create CSV content with tipo_parte
        csv_content = f"""nome_caso,numero_cnj,status,advogado_oab,tipo_parte
"Bulk Test - AUTOR",111111111111111111,ATIVO,{oab1},autor
"Bulk Test - REU",222222222222222222,PENDENTE,{oab2},reu
"Bulk Test - TERCEIRO",333333333333333333,ATIVO,{oab1},terceiro"""
        
        print_info(f"CSV content to upload:\n{csv_content}\n")
        
        # Upload
        result = manager.bulk_create_processos_from_csv(id_cliente, csv_content)
        
        print_info(f"Upload result: {result['status']}")
        print_info(f"Processos criados: {result['processos_criados']}")
        
        if result['erros']:
            print_warning(f"Erros encontrados:")
            for erro in result['erros']:
                print_warning(f"  - {erro}")
        
        if result['ids_criados']:
            print_success(f"IDs criados: {result['ids_criados']}")
            return True, result['ids_criados']
        else:
            print_error("No processes created")
            return False
            
    except Exception as e:
        print_error(f"Bulk upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_data_verification():
    """Test 5: Verify tipo_parte Data in Database"""
    print_header("TEST 5: Data Verification - tipo_parte in Database")
    
    try:
        manager = CadastroManager()
        
        # Query processes with tipo_parte
        query = """
        SELECT id_processo, nome_caso, tipo_parte, advogado_oab, status
        FROM processos 
        WHERE tipo_parte IS NOT NULL 
        ORDER BY data_inicio DESC 
        LIMIT 10
        """
        
        result = manager._execute_query(query, fetch="all")
        
        if result:
            print_success(f"Found {len(result)} processes with tipo_parte")
            print_info("\nRecent processes with tipo_parte:")
            print(f"\n{'ID':<20} | {'Nome Caso':<30} | {'Tipo Parte':<12} | {'Status':<10}")
            print("-" * 75)
            
            for row in result:
                print(f"{row['id_processo']:<20} | {row['nome_caso'][:28]:<30} | {row['tipo_parte']:<12} | {row['status']:<10}")
            
            # Statistics
            stats_query = """
            SELECT tipo_parte, COUNT(*) as count
            FROM processos 
            WHERE tipo_parte IS NOT NULL 
            GROUP BY tipo_parte 
            ORDER BY count DESC
            """
            stats = manager._execute_query(stats_query, fetch="all")
            
            print_info("\nDistribution by tipo_parte:")
            for row in stats:
                print_info(f"  {row['tipo_parte']}: {row['count']} processes")
            
            return True
        else:
            print_warning("No processes with tipo_parte found yet")
            return True
            
    except Exception as e:
        print_error(f"Data verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_case_insensitivity():
    """Test 6: Case Insensitivity - tipo_parte normalization"""
    print_header("TEST 6: Case Insensitivity and Normalization")
    
    try:
        manager = CadastroManager()
        
        # Get real client and advogado
        clientes = manager.get_clientes()
        advogados = manager.get_advogados()
        
        if not clientes or not advogados:
            print_error("Need clients and advogados")
            return False
        
        id_cliente = clientes[0]['id_cliente']
        advogado_oab = advogados[0]['oab']
        
        # Test different cases
        test_cases = [
            ("AUTOR", "autor"),      # uppercase -> lowercase
            ("Reu", "reu"),          # mixed case -> lowercase
            ("TERCEIRO", "terceiro"), # uppercase -> lowercase
        ]
        
        for input_tipo, expected_tipo in test_cases:
            dados = {
                "id_cliente": id_cliente,
                "nome_caso": f"Case Test {input_tipo} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "numero_cnj": None,
                "status": "PENDENTE",
                "advogado_oab": advogado_oab,
                "tipo_parte": input_tipo
            }
            
            proc_id = manager.save_processo(dados)
            
            # Verify stored value
            processo = manager.get_processo_by_id(proc_id)
            stored_tipo = processo['tipo_parte']
            
            if stored_tipo == expected_tipo:
                print_success(f"'{input_tipo}' normalized to '{stored_tipo}' ✓")
            else:
                print_error(f"'{input_tipo}' stored as '{stored_tipo}' (expected '{expected_tipo}')")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Case insensitivity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print_header("TIPO_PARTE FEATURE - COMPREHENSIVE TEST SUITE")
    print_info(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Database: {os.getenv('DB_NAME')}")
    print_info(f"Host: {os.getenv('DB_HOST')}")
    
    results = {}
    
    # Test 1: Connection
    print_header("Starting Tests...")
    results['Connection'] = test_1_database_connection()
    
    if not results['Connection']:
        print_error("Cannot continue - database connection failed")
        return results
    
    # Test 2: Helper Functions
    results['Helpers'] = test_2_helper_functions()
    
    # Test 3: Single Process
    test3_result = test_3_single_processo_creation()
    results['Single Process'] = test3_result is not False
    
    # Test 4: Bulk Upload
    test4_result = test_4_bulk_csv_upload()
    results['Bulk Upload'] = test4_result is not False
    
    # Test 5: Data Verification
    results['Data Verification'] = test_5_data_verification()
    
    # Test 6: Case Insensitivity
    results['Case Insensitivity'] = test_6_case_insensitivity()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{test_name:<25} {status}")
    
    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print_success(f"All {total} tests PASSED! 🎉")
        return True
    else:
        print_error(f"{total - passed} test(s) FAILED")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
