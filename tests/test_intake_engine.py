import sys
import os
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intake_engine import SemanticSanityFilter, IntakeCompletenessScorer, AdaptiveBusinessInterviewer, IntakeEngine
from src.orchestration.captain import CaptainOrchestrator

def test_gibberish_rejection_short():
    res = SemanticSanityFilter.validate_narrative("make database")
    assert res["valid"] is False
    assert res["reason"] == "REJECT_INSUFFICIENT_LENGTH"

def test_gibberish_rejection_repetitive():
    res = SemanticSanityFilter.validate_narrative("asdf asdf asdf asdf asdf")
    assert res["valid"] is False
    assert res["reason"] == "REJECT_GIBBERISH_DETECTED"

def test_contradiction_detection_oltp_vs_monthly_rollup():
    narrative = "A live checkout cart with sub-millisecond row lock where we need monthly snapshot balance rollups."
    res = SemanticSanityFilter.validate_narrative(narrative)
    assert res["valid"] is False
    assert res["reason"] == "FLAG_CONTRADICTION"

def test_incomplete_narrative_triggers_targeted_questions():
    raw_narrative = "A customer places an order for a product from a retail store."
    res = IntakeEngine.process_intake(raw_narrative)
    
    assert res["status"] == "NEEDS_CLARIFICATION"
    assert res["completeness_score"] < 100.0
    assert len(res["questions"]) > 0
    assert "workload_intent" in res["missing_vectors"]

def test_incomplete_narrative_hard_blocks_spec_generation_in_captain():
    captain = CaptainOrchestrator()
    # Narrative is only partially complete (missing workload intent and temporal policy)
    payload = {
        "domain": "ecommerce",
        "narrative": "A customer places an order for a product from a retail store."
    }
    result = captain.execute_workflow(payload)
    
    # Must hard-block and not generate SQL DDL or STTM
    assert result["status"] == "INTAKE_INCOMPLETE_BLOCKED"
    assert result["completeness_score"] < 100.0
    assert "generated_sql" not in result
    assert "sttm_markdown" not in result
    assert len(result["questions"]) > 0

def test_enriched_narrative_reaches_100_percent_certified_ready():
    raw_narrative = "A customer places an order for a product from a retail store."
    business_answers = [
        "We want to build executive dashboards, BI reports, and analyze sales trends over time.",
        "Past historical reports should preserve the original customer address at the time of purchase so past regional sales remain accurate.",
        "No, we only need to record each individual transaction as a single standalone event."
    ]
    res = IntakeEngine.process_intake(raw_narrative, business_answers)
    
    assert res["status"] == "CERTIFIED_READY"
    assert res["completeness_score"] == 100.0
    assert res["architecture_decision"]["pattern"] == "KIMBALL_STAR_SCD2"
    assert len(res["questions"]) == 0

def test_captain_orchestrator_rejects_gibberish():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "ecommerce",
        "narrative": "asdf asdf asdf asdf"
    }
    result = captain.execute_workflow(payload)
    assert result["status"] == "REJECTED_INPUT_INVALID"
    assert "rejection_reason" in result

def test_captain_orchestrator_executes_only_when_100_percent():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "ecommerce",
        "narrative": "A customer browses products online and places an order. The order is fulfilled from a local retail store or shipped from a regional warehouse.",
        "business_answers": [
            "We want to build executive dashboards, BI reports, and analyze sales trends over time.",
            "Always overwrite past records with their newest address everywhere across the system.",
            "We need to track how long it takes to move across stages from Order Placed to Picked to Shipped to Delivered."
        ]
    }
    result = captain.execute_workflow(payload)
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert result["architecture_pattern"] == "ACCUMULATING_SNAPSHOT_FACT"
    assert result["intake_completeness_score"] == 100.0
    assert result["quality_index"] >= 98.0
    assert "generated_sql" in result
    assert "sttm_markdown" in result
