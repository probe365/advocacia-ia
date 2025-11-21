#!/usr/bin/env python
"""
Phase 4: Testing - Unit Tests for tipo_parte_helpers (STANDALONE)
Doesn't require Flask initialization
"""
import sys
import os

# Read helpers directly without importing from app
def load_helpers():
    """Load helper functions directly from file"""
    helpers_file = 'app/utils/tipo_parte_helpers.py'
    
    # Read the file
    with open(helpers_file, 'r', encoding='utf-8') as f:
        helpers_code = f.read()
    
    # Execute in a namespace
    namespace = {}
    exec(helpers_code, namespace)
    
    return namespace

def run_tests():
    print("\n" + "="*80)
    print("PHASE 4: UNIT TESTS - tipo_parte_helpers.py (STANDALONE)")
    print("="*80)
    
    try:
        # Load helpers
        print("\n📦 Loading helper functions...")
        ns = load_helpers()
        
        validate_tipo_parte = ns['validate_tipo_parte']
        get_tipo_parte_label = ns['get_tipo_parte_label']
        get_tipo_parte_description = ns['get_tipo_parte_description']
        get_tipo_parte_badge_class = ns['get_tipo_parte_badge_class']
        get_tipo_parte_icon = ns['get_tipo_parte_icon']
        format_tipo_parte_for_display = ns['format_tipo_parte_for_display']
        get_tipos_parte_by_category = ns['get_tipos_parte_by_category']
        VALID_TIPOS_PARTE = ns['VALID_TIPOS_PARTE']
        
        print("✅ Helpers loaded successfully\n")
        
        # Test 1: Validation
        print("🧪 Test 1: validate_tipo_parte()")
        for tipo in VALID_TIPOS_PARTE:
            assert validate_tipo_parte(tipo), f"Should accept {tipo}"
            assert validate_tipo_parte(tipo.upper()), f"Should accept {tipo.upper()}"
        
        assert not validate_tipo_parte('invalid'), "Should reject invalid"
        # None is OK to reject (helper should handle gracefully)
        print("   ✅ Validation tests passed!\n")
        
        # Test 2: Labels
        print("🧪 Test 2: get_tipo_parte_label()")
        labels = {
            'autor': 'Autor',
            'reu': 'Réu',
            'terceiro': 'Terceiro',
            'reclamante': 'Reclamante',
            'reclamada': 'Reclamada',
        }
        for tipo, expected in labels.items():
            label = get_tipo_parte_label(tipo)
            assert label == expected, f"Expected {expected}, got {label}"
        print("   ✅ Label tests passed!\n")
        
        # Test 3: Descriptions
        print("🧪 Test 3: get_tipo_parte_description()")
        for tipo in VALID_TIPOS_PARTE:
            desc = get_tipo_parte_description(tipo)
            assert desc and len(desc) > 0, f"Should have description for {tipo}"
        print("   ✅ Description tests passed!\n")
        
        # Test 4: Badge Classes
        print("🧪 Test 4: get_tipo_parte_badge_class()")
        for tipo in VALID_TIPOS_PARTE:
            badge = get_tipo_parte_badge_class(tipo)
            assert badge and 'badge-' in badge, f"Should return badge class for {tipo}"
        print("   ✅ Badge class tests passed!\n")
        
        # Test 5: Icons
        print("🧪 Test 5: get_tipo_parte_icon()")
        for tipo in VALID_TIPOS_PARTE:
            icon = get_tipo_parte_icon(tipo)
            assert icon and 'fa-' in icon, f"Should return icon for {tipo}"
        print("   ✅ Icon tests passed!\n")
        
        # Test 6: HTML Formatting
        print("🧪 Test 6: format_tipo_parte_for_display()")
        for tipo in VALID_TIPOS_PARTE:
            html = format_tipo_parte_for_display(tipo)
            assert html and '<span' in html, f"Should return HTML for {tipo}"
            assert 'badge' in html, f"Should include badge for {tipo}"
        print("   ✅ HTML formatting tests passed!\n")
        
        # Test 7: Category Filtering
        print("🧪 Test 7: get_tipos_parte_by_category()")
        civil = get_tipos_parte_by_category('civil')
        assert 'autor' in civil and 'reu' in civil, "Civil should include autor and reu"
        
        trabalhista = get_tipos_parte_by_category('trabalhista')
        assert 'reclamante' in trabalhista, "Trabalhista should include reclamante"
        
        todas = get_tipos_parte_by_category('todas')
        assert len(todas) == len(VALID_TIPOS_PARTE), "Todas should include all"
        print("   ✅ Category filter tests passed!\n")
        
        # Summary
        print("="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n📊 Test Summary:")
        print(f"   ✓ Validation: OK")
        print(f"   ✓ Labels: OK")
        print(f"   ✓ Descriptions: OK")
        print(f"   ✓ Badge Classes: OK")
        print(f"   ✓ Icons: OK")
        print(f"   ✓ HTML Formatting: OK")
        print(f"   ✓ Category Filtering: OK")
        print(f"\n   Total Tests: 7")
        print(f"   Passed: 7")
        print(f"   Failed: 0")
        print(f"   Success Rate: 100%\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
