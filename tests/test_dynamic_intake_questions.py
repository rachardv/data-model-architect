import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noun_verb_parser import NounVerbSemanticParser
from src.intake_engine import AdaptiveBusinessInterviewer, IntakeEngine

def test_extract_domain_roles_driver_license():
    narrative = 'i want to analyze the number of open appointment slots availability for driver licence offices'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    assert roles['primary_event'] == 'appointment slot'
    assert roles['primary_actor'] == 'driver'
    assert roles['resource_location'] == 'driver license office'

def test_extract_domain_roles_ecommerce():
    narrative = 'A customer places an order for a product from a retail store.'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    assert roles['primary_event'] == 'order'
    assert roles['primary_actor'] == 'customer'
    assert roles['resource_location'] == 'store'

def test_extract_domain_roles_healthcare():
    narrative = 'Patients schedule appointment visits with doctors at medical clinics.'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    assert roles['primary_actor'] == 'patient'
    assert roles['resource_location'] == 'clinic'
    assert roles['primary_event'] in ['appointment slot', 'appointment', 'visit']

def test_dynamic_questions_driver_license():
    narrative = 'i want to analyze the number of open appointment slots availability for driver licence offices'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    questions = AdaptiveBusinessInterviewer.get_questions_for_missing_vectors(
        ['workload_intent', 'entity_grain', 'temporal_policy', 'lifecycle_funnel', 'relationship_multiplicity'],
        domain_roles=roles
    )
    
    assert len(questions) == 5
    q_map = {q['id']: q for q in questions}
    
    # 1. Workload Intent contains appointment slot & driver license offices
    q_workload = q_map['q_workload_intent']
    assert 'appointment slot' in q_workload['question']
    assert any('driver license offices' in opt for opt in q_workload['options'])
    
    # 2. Entity Grain contains appointment slots & driver
    q_grain = q_map['q_entity_grain']
    assert 'appointment slots' in q_grain['question']
    assert any('driver' in opt for opt in q_grain['options'])
    
    # 3. Temporal Policy contains driver license office
    q_temporal = q_map['q_temporal_policy']
    assert 'driver license office' in q_temporal['question']
    assert any('driver license office' in opt for opt in q_temporal['options'])
    
    # 4. Lifecycle Funnel contains Periodic Daily Snapshots for offices
    q_lifecycle = q_map['q_lifecycle_funnel']
    assert 'appointment slots' in q_lifecycle['question']
    assert any('Periodic Daily Snapshots' in opt and 'driver license office' in opt for opt in q_lifecycle['options'])
    
    # 5. Relationship Multiplicity contains driver & appointment slot
    q_multi = q_map['q_relationship_multiplicity']
    assert 'appointment slot' in q_multi['question']
    assert any('1 primary driver' in opt for opt in q_multi['options'])

def test_dynamic_questions_multi_event_bus_matrix():
    narrative = 'Drivers book appointment slots for road tests at license offices and pay test fees at counters.'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    assert len(roles['secondary_events']) > 0 or 'fee' in roles['secondary_events']
    
    q_grain = AdaptiveBusinessInterviewer.build_dynamic_question('entity_grain', domain_roles=roles)
    # Must offer the Multi-Fact Bus Matrix option
    assert any('Multi-Fact Bus Matrix' in opt for opt in q_grain['options'])

def test_vague_prompt_fallback():
    narrative = 'analyze trends'
    roles = NounVerbSemanticParser.extract_domain_roles(narrative)
    
    questions = AdaptiveBusinessInterviewer.get_questions_for_missing_vectors(
        ['workload_intent', 'entity_grain', 'temporal_policy', 'lifecycle_funnel', 'relationship_multiplicity'],
        domain_roles=roles
    )
    
    assert len(questions) == 5
    for q in questions:
        assert q['question']
        assert len(q['options']) >= 2
        for opt in q['options']:
            assert 'None' not in opt
            assert len(opt) > 10

def test_intake_engine_process_intake_injects_dynamic_questions():
    narrative = 'i want to analyze the number of open appointment slots availability for driver licence offices'
    res = IntakeEngine.process_intake(narrative)
    
    assert res['status'] == 'NEEDS_CLARIFICATION'
    assert len(res['questions']) > 0
    for q in res['questions']:
        joined_text = q['question'] + ' ' + ' '.join(q['options'])
        assert any(k in joined_text for k in ['appointment', 'driver', 'office', 'slot'])
