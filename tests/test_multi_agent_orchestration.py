import pytest
from src.orchestration.captain import CaptainOrchestrator
from src.orchestration.spawner import SubagentSpawner
from src.orchestration.reviewer_council import ReviewerCouncil

def test_captain_orchestration_lifecycle():
    captain = CaptainOrchestrator()
    
    payload = {
        "domain": "ecommerce",
        "branch": "NEW_MODEL",
        "narrative": "A customer places an order on our e-commerce platform. The warehouse worker ships the package.",
        "usage_params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        }
    }
    
    result = captain.execute_workflow(payload)
    
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert result["architecture_pattern"] == "KIMBALL_STAR_SCD2"
    assert result["quality_index"] >= 95.0
    assert result["spawner_log_count"] >= 5
    assert any("customer" in t for t in result["generated_sql"])
    assert any("orders" in t for t in result["generated_sql"])
    assert "erDiagram" in result["erd_markdown"]
    assert "Enterprise Data Contract" in result["contract_markdown"]

def test_reviewer_council_flags_discount_multiplication():
    flawed_schema = {
        "tables": [
            {
                "name": "fact_order_items",
                "columns": [
                    {"name": "order_item_id", "type": "BIGINT"},
                    {"name": "order_discount_amount", "type": "DECIMAL(14,2)"}
                ]
            }
        ]
    }
    
    audit = ReviewerCouncil.audit_model(flawed_schema)
    assert audit["status"] == "CHANGES_REQUIRED"
    assert audit["findings_count"] == 1
    assert audit["findings"][0]["reviewer"] == "financial_risk_reviewer"
    assert "Multiplication" in audit["findings"][0]["title"]
