import pytest
from src.orchestration.captain import CaptainOrchestrator, WorkflowMode

def test_captain_tracks_new_model_mode():
    captain = CaptainOrchestrator(output_dir="docs")
    res = captain.execute_workflow({
        "domain": "retail_test",
        "narrative": "Customers buy products at store"
    })
    
    assert res["active_mode"] == WorkflowMode.NEW_MODEL.value
    assert "session_id" in res
    assert captain.active_session is not None
    assert captain.active_session.mode == WorkflowMode.NEW_MODEL

def test_captain_tracks_add_business_rules_mode():
    captain = CaptainOrchestrator(output_dir="docs")
    res = captain.execute_workflow({
        "branch": "ADD_BUSINESS_RULES",
        "domain": "retail_test",
        "narrative": "Customers buy products at store",
        "rules": [{"description": "Total > 0", "definition": "total > 0"}]
    })
    
    assert res["active_mode"] == WorkflowMode.ADD_BUSINESS_RULES.value
    assert captain.active_session.mode == WorkflowMode.ADD_BUSINESS_RULES

def test_captain_resumes_session_across_turns_and_accumulates_answers():
    captain = CaptainOrchestrator(output_dir="docs")
    
    # Turn 1: Partial narrative (20% score) -> Blocked
    turn1_res = captain.execute_workflow({
        "domain": "coffee_shop",
        "narrative": "We want to analyze our company performance and business metrics over time."
    })
    
    assert turn1_res["status"] == "INTAKE_INCOMPLETE_BLOCKED"
    session_id = turn1_res["session_id"]
    assert turn1_res["active_mode"] == WorkflowMode.NEW_MODEL.value
    
    # Turn 2: Supply follow-up answers with the same session_id -> reaches 100%
    turn2_res = captain.execute_workflow({
        "session_id": session_id,
        "narrative": "We want to analyze our company performance and business metrics over time.",
        "business_answers": [
            "We do car insurance policies, vehicle coverage, and policyholder premium payments for product sales.",
            "Simple Single-Driver Model: Strictly 1 named driver per insurance policy with standard one-to-one ownership.",
            "No multi-stage turnaround tracking, single standalone transaction events.",
            "Historical reports should preserve their original address and profile at the exact time of each event so past regional sales remain accurate (SCD Type 2)."
        ]
    })
    
    assert turn2_res["session_id"] == session_id
    assert turn2_res["active_mode"] == WorkflowMode.NEW_MODEL.value
    assert turn2_res["status"] == "CERTIFIED_PRODUCTION_READY"
    assert turn2_res["intake_completeness_score"] == 100.0
    assert len(turn2_res["accumulated_answers"]) == 4
