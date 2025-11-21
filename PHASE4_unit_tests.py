#!/usr/bin/env python
"""
Phase 4: Testing - Unit Tests for tipo_parte_helpers
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.tipo_parte_helpers import (
    validate_tipo_parte,
    get_tipo_parte_label,
    get_tipo_parte_description,
    get_tipo_parte_badge_class,
    get_tipo_parte_icon,
    format_tipo_parte_for_display,
    get_tipos_parte_by_category,
    VALID_TIPOS_PARTE
)

def test_validate_tipo_parte():
    """Test validation function"""
    print("\n🧪 Testing: validate_tipo_parte()")
    
    # Valid values
    for tipo in VALID_TIPOS_PARTE:
        assert validate_tipo_parte(tipo), f"Should accept {tipo}"
        assert validate_tipo_parte(tipo.upper()), f"Should accept uppercase {tipo}"
    
    # Invalid values
    invalid = ['invalid', 'cliente', 'plaintiff', '', None]
    for tipo in invalid:
        assert not validate_tipo_parte(tipo), f"Should reject {tipo}"
    
    print("   ✅ All validation tests passed!")

def test_get_tipo_parte_label():
    """Test label translation"""
    print("\n🧪 Testing: get_tipo_parte_label()")
    
    labels = {
        'autor': 'Autor',
        'reu': 'Réu',
        'terceiro': 'Terceiro',
        'reclamante': 'Reclamante',
        'reclamada': 'Reclamada',
    }
    
    for tipo, expected_label in labels.items():
        label = get_tipo_parte_label(tipo)
        assert label == expected_label, f"Label for {tipo} should be {expected_label}, got {label}"
    
    # Case insensitive
    assert get_tipo_parte_label('AUTOR') == 'Autor'
    
    # Invalid returns None or empty
    assert get_tipo_parte_label('invalid') is None or get_tipo_parte_label('invalid') == ''
    
    print("   ✅ All label tests passed!")

def test_get_tipo_parte_description():
    """Test description retrieval"""
    print("\n🧪 Testing: get_tipo_parte_description()")
    
    for tipo in VALID_TIPOS_PARTE:
        desc = get_tipo_parte_description(tipo)
        assert desc and len(desc) > 0, f"Should have description for {tipo}"
    
    # Invalid returns None or empty
    result = get_tipo_parte_description('invalid')
    assert result is None or result == '', "Should return None/empty for invalid tipo"
    
    print("   ✅ All description tests passed!")

def test_get_tipo_parte_badge_class():
    """Test badge CSS class assignment"""
    print("\n🧪 Testing: get_tipo_parte_badge_class()")
    
    for tipo in VALID_TIPOS_PARTE:
        badge_class = get_tipo_parte_badge_class(tipo)
        assert badge_class and 'badge' in badge_class, f"Should return badge class for {tipo}"
        assert badge_class.startswith('badge-'), f"Should start with 'badge-' for {tipo}"
    
    print("   ✅ All badge class tests passed!")

def test_get_tipo_parte_icon():
    """Test icon assignment"""
    print("\n🧪 Testing: get_tipo_parte_icon()")
    
    for tipo in VALID_TIPOS_PARTE:
        icon = get_tipo_parte_icon(tipo)
        assert icon and 'fa-' in icon, f"Should return Font Awesome icon for {tipo}"
    
    print("   ✅ All icon tests passed!")

def test_format_tipo_parte_for_display():
    """Test HTML formatting"""
    print("\n🧪 Testing: format_tipo_parte_for_display()")
    
    for tipo in VALID_TIPOS_PARTE:
        html = format_tipo_parte_for_display(tipo)
        assert '<span' in html, f"Should return HTML span for {tipo}"
        assert 'badge' in html, f"Should include badge class for {tipo}"
        assert 'fa-' in html, f"Should include icon for {tipo}"
        
        # Check it contains the label
        label = get_tipo_parte_label(tipo)
        assert label in html, f"Should contain label {label} in HTML"
    
    # Invalid returns safe value
    html = format_tipo_parte_for_display('invalid')
    assert html is None or html == '' or 'span' not in html
    
    print("   ✅ All HTML formatting tests passed!")

def test_get_tipos_parte_by_category():
    """Test category filtering"""
    print("\n🧪 Testing: get_tipos_parte_by_category()")
    
    civil = get_tipos_parte_by_category('civil')
    assert 'autor' in civil, "Civil should include autor"
    assert 'reu' in civil, "Civil should include reu"
    assert 'reclamante' not in civil, "Civil should not include reclamante"
    
    trabalhista = get_tipos_parte_by_category('trabalhista')
    assert 'reclamante' in trabalhista, "Trabalhista should include reclamante"
    assert 'reclamada' in trabalhista, "Trabalhista should include reclamada"
    
    todas = get_tipos_parte_by_category('todas')
    assert len(todas) == len(VALID_TIPOS_PARTE), "Todas should include all"
    
    print("   ✅ All category tests passed!")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("PHASE 4: UNIT TESTS - tipo_parte_helpers.py")
    print("="*80)
    
    try:
        test_validate_tipo_parte()
        test_get_tipo_parte_label()
        test_get_tipo_parte_description()
        test_get_tipo_parte_badge_class()
        test_get_tipo_parte_icon()
        test_format_tipo_parte_for_display()
        test_get_tipos_parte_by_category()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*80 + "\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*80 + "\n")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
