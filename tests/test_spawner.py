import sys
import os
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestration.spawner import SubagentSpawner
from src.orchestration.captain import CaptainOrchestrator

def test_spawner_registers_all_micro_agents():
    spawner = SubagentSpawner()
    expected_agents = [
        "captain_orchestrator",
        "requirements_architect_agent",
        "semantic_scribe_agent",
        "completeness_auditor_agent",
        "business_interviewer_agent",
        "data_model_architect_agent",
        "financial_risk_reviewer",
        "temporal_risk_reviewer",
        "relational_risk_reviewer",
        "refactor_risk_reviewer"
    ]
    for agent in expected_agents:
        assert agent in spawner.REGISTERED_AGENTS

def test_dispatch_intake_squad():
    spawner = SubagentSpawner()
    squad = spawner.dispatch_intake_squad("A customer places an order online.")
    assert len(squad) == 3
    assert "semantic_scribe_agent" in squad
    assert "completeness_auditor_agent" in squad
    assert "business_interviewer_agent" in squad
    assert len(spawner.message_log) == 3

def test_captain_executes_intake_squad_end_to_end():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "retail",
        "narrative": "A customer places an order for a product from a retail store.",
        "business_answers": [
            "We want to build executive dashboards, BI reports, and analyze sales trends over time.",
            "Past historical reports should preserve the original customer address at the time of purchase.",
            "No, we only need to record each individual transaction as a single standalone event."
        ]
    }
    result = captain.execute_workflow(payload)
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert result["spawner_log_count"] >= 8  # Intake squad (3) + Requirements (1) + Architect (1) + 4 Reviewers (4)
