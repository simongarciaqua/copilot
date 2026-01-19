#!/usr/bin/env python3
"""
Test script for the rules engine
Tests different customer contexts to verify rules are correctly evaluated
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rules_engine import load_rules_engine


def test_scenario(name, context, expected_decision=None, expected_stop_allowed=None):
    """Test a scenario and print results"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    print(f"Context: {context}")
    
    try:
        engine = load_rules_engine("STOP_REPARTO")
        result = engine.evaluate(context)
        
        print(f"\n✅ Rules Engine Result:")
        print(f"   Decision: {result.get('decision')}")
        print(f"   Stop Allowed: {result.get('stop_allowed')}")
        print(f"   Allowed Actions: {result.get('allowed_actions', [])}")
        print(f"   Reason: {result.get('reason')}")
        
        if 'allow_stop_0euros' in result:
            print(f"   Allow Stop 0€: {result.get('allow_stop_0euros')}")
        
        # Validation
        passed = True
        if expected_decision and result.get('decision') != expected_decision:
            print(f"\n❌ FAILED: Expected decision '{expected_decision}', got '{result.get('decision')}'")
            passed = False
        
        if expected_stop_allowed is not None and result.get('stop_allowed') != expected_stop_allowed:
            print(f"\n❌ FAILED: Expected stop_allowed {expected_stop_allowed}, got {result.get('stop_allowed')}")
            passed = False
        
        if passed:
            print(f"\n✅ PASSED")
        
        return passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("RULES ENGINE TESTS")
    print("="*60)
    
    results = []
    
    # Test 1: Exceso de agua + Plan Ahorro = Reconducción obligatoria
    results.append(test_scenario(
        "Exceso de agua en Plan Ahorro - Reconducción obligatoria",
        {
            "plan": "Ahorro",
            "scoring": 3.5,
            "motivo": "exceso_agua",
            "stops_ultimo_ano": 1
        },
        expected_decision="reconduccion",
        expected_stop_allowed=False
    ))
    
    # Test 2: Ausencia/Vacaciones = Stop permitido
    results.append(test_scenario(
        "Ausencia por vacaciones - Stop permitido",
        {
            "motivo": "ausencia_vacaciones",
            "scoring": 3.0,
            "plan": "Estandar"
        },
        expected_decision="retencion",
        expected_stop_allowed=True
    ))
    
    # Test 3: Scoring alto = Stop 0€ permitido
    results.append(test_scenario(
        "Scoring alto - Stop a 0€ permitido",
        {
            "scoring": 4.5,
            "stops_0euros_ultimo_ano": 0,
            "plan": "Premium"
        },
        expected_decision="no_match",  # No primary decision, just flag
        expected_stop_allowed=None
    ))
    
    # Test 4: Scoring alto pero límite alcanzado
    results.append(test_scenario(
        "Scoring alto pero límite stops 0€ alcanzado",
        {
            "scoring": 4.2,
            "stops_0euros_ultimo_ano": 2,  # Más de 1
            "plan": "Premium"
        },
        expected_decision="no_match",
        expected_stop_allowed=None
    ))
    
    # Test 5: Sin reglas que apliquen
    results.append(test_scenario(
        "Sin reglas aplicables",
        {
            "motivo": "otro_motivo",
            "plan": "Estandar",
            "scoring": 2.5
        },
        expected_decision="no_match",
        expected_stop_allowed=None
    ))
    
    # Test 6: Múltiples reglas (exceso agua + scoring alto)
    results.append(test_scenario(
        "Múltiples reglas aplicables - Exceso agua + Scoring alto",
        {
            "plan": "Ahorro",
            "motivo": "exceso_agua",
            "scoring": 4.5,
            "stops_0euros_ultimo_ano": 0
        },
        expected_decision="reconduccion",  # Primary rule
        expected_stop_allowed=False
    ))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
