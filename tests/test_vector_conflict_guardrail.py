import pytest
import os
from src.intake_engine import VectorConflictDetector, IntakeEngine
from src.orchestration.captain import CaptainOrchestrator

def test_grain_conflict_detection():
    rules = [
        {"description": "Shipping fee of at least $5.00 applies to each order total", "definition": "shipping_fee >= 5.00"}
    ]
    baseline_vectors = {"entity_grain": "LINE_ITEM"}
    res = VectorConflictDetector.detect_conflicts(rules, baseline_vectors)
    
    assert res is not None
    assert res["conflict_count"] == 1
    assert res["primary_conflict"]["vector_violated"] == "entity_grain"
    assert "Risk of severe revenue" in res["primary_conflict"]["business_risk"]
    assert "ADD_COMPANION_MART" in res["alert"]
    assert "FULL_REFACTOR" in res["alert"]

def test_multiplicity_conflict_detection():
    rules = [
        {"description": "Policy supports multiple drivers with co-driver allocation", "definition": "co_driver_count <= 5"}
    ]
    baseline_vectors = {"relationship_multiplicity": "ONE_TO_ONE"}
    res = VectorConflictDetector.detect_conflicts(rules, baseline_vectors)
    
    assert res is not None
    assert res["primary_conflict"]["vector_violated"] == "relationship_multiplicity"
    assert "double-counting" in res["primary_conflict"]["business_risk"]

def test_temporal_conflict_detection():
    rules = [
        {"description": "Preserve history and point-in-time audit for all customer tier updates", "definition": "scd_valid_to IS NOT NULL"}
    ]
    baseline_vectors = {"temporal_policy": "SCD1_OVERWRITE"}
    res = VectorConflictDetector.detect_conflicts(rules, baseline_vectors)
    
    assert res is not None
    assert res["primary_conflict"]["vector_violated"] == "temporal_policy"
    assert "audit regulations" in res["primary_conflict"]["business_risk"]

def test_captain_halts_with_awaiting_confirmation():
    captain = CaptainOrchestrator(output_dir="docs")
    res = captain.execute_workflow({
        "domain": "retail_store",
        "narrative": "Customer buys products at checkout store",
        "baseline_vectors": {"entity_grain": "LINE_ITEM"},
        "rules": [
            {"description": "Shipping fee of $5.00 on order total", "definition": "shipping_fee >= 5.00"}
        ]
    })
    
    assert res["status"] == "AWAITING_ARCHITECTURAL_CONFIRMATION"
    assert res["state"] == "TRIAGE_AWAITING_CONFIRMATION"
    assert "ARCHITECTURAL CONFLICT DETECTED" in res["alert"]
    assert len(res["options"]) == 2
    assert res["options"][0]["id"] == "ADD_COMPANION_MART"
    assert res["options"][1]["id"] == "FULL_REFACTOR"

def test_captain_resolves_with_add_companion_mart():
    captain = CaptainOrchestrator(output_dir="docs")
    res = captain.execute_workflow({
        "domain": "retail_store",
        "narrative": "Customer buys products at checkout store. We want to build executive dashboards and analyze business trends over time.",
        "business_answers": [
            "Detailed product sales & shopping cart line items.",
            "Historical reports should preserve their original address and profile at the exact time of each event (SCD Type 2).",
            "No, single standalone transaction events.",
            "Standard one-to-one ownership."
        ],
        "baseline_vectors": {"entity_grain": "LINE_ITEM"},
        "rules": [
            {"description": "Shipping fee of $5.00 on order total", "definition": "shipping_fee >= 5.00"}
        ],
        "architectural_choice": "ADD_COMPANION_MART"
    })
    
    assert res["status"] == "CERTIFIED_PRODUCTION_READY"
    assert res["resolution_applied"] == "ENTERPRISE_BUS_ADDITIVE_EXPANSION"
    
    # Verify the companion table was added to generated_sql
    assert "fact_retail_store_orders_summary" in res["generated_sql"]
    assert "shipping_fee_usd" in res["generated_sql"]["fact_retail_store_orders_summary"]

def test_captain_resolves_with_full_refactor():
    captain = CaptainOrchestrator(output_dir="docs")
    res = captain.execute_workflow({
        "domain": "retail_store",
        "narrative": "Customer buys products at checkout store. We want to build executive dashboards and analyze business trends over time.",
        "business_answers": [
            "Detailed product sales & shopping cart line items.",
            "Historical reports should preserve their original address and profile at the exact time of each event (SCD Type 2).",
            "No, single standalone transaction events.",
            "Standard one-to-one ownership."
        ],
        "baseline_vectors": {"entity_grain": "LINE_ITEM"},
        "rules": [
            {"description": "Shipping fee of $5.00 on order total", "definition": "shipping_fee >= 5.00"}
        ],
        "architectural_choice": "FULL_REFACTOR"
    })
    
    assert res["status"] == "CERTIFIED_PRODUCTION_READY"
    assert res["resolution_applied"] == "FULL_MODEL_REFACTOR_MIGRATION"
    assert "migration_artifacts" in res
    assert os.path.exists(res["migration_artifacts"]["backfill_sql_path"])
    assert os.path.exists(res["migration_artifacts"]["downstream_impact_report_path"])
