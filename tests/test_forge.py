import pytest
from src.forge import ForgeEngineRunner
from src.forge_intake import ForgeIntakeEngine
from src.forge_reward import ForgeWeightAdjuster

def test_forge_engine_certification_suite():
    """Validates full execution of the Forge Workflow certification battery with rewards and weights."""
    sc = ForgeEngineRunner.run_forge_certification()
    
    assert sc["workflow"] == "FORGE_ENGINE_CERTIFICATION"
    assert sc["overall_status"] == "PASS"
    assert sc["total_verifications_executed"] >= 200
    
    # 1. Predefined Gate
    assert sc["predefined_benchmark_gate"] is not None
    assert sc["predefined_benchmark_gate"]["status"] in ["PASS", "EMPTY_CATALOG"]
    
    # 2. Industry Standards Gate
    assert sc["industry_standards_gate"] is not None
    assert sc["industry_standards_gate"]["overall_status"] == "PASS"
    assert sc["industry_standards_gate"]["ssb"]["status"] == "PASS"
    assert sc["industry_standards_gate"]["tpcds"]["status"] == "PASS"
    assert sc["industry_standards_gate"]["tpcdi"]["status"] == "PASS"
    assert sc["industry_standards_gate"]["tpch"]["status"] == "PASS"
    
    # 3. Academic Semantics Gate
    assert sc["semantic_benchmarks_gate"] is not None
    assert sc["semantic_benchmarks_gate"]["overall_status"] == "PASS"
    assert sc["semantic_benchmarks_gate"]["scenarios_passed"] == 25

    # 4. Forge Reward Signals
    assert sc["reward_signals"] is not None
    assert sc["reward_signals"]["composite_reward"] >= 0.95
    assert sc["reward_signals"]["metric_conservation_reward"] == 1.0

    # 5. Adjusted Studio Policy Weights
    assert sc["adjusted_studio_weights"] is not None
    assert sc["adjusted_studio_weights"]["version"] >= 1
    assert "quarantine_strictness" in sc["adjusted_studio_weights"]

def test_forge_intake_decoupled():
    """Verifies that Forge intake is machine-driven and decoupled from human dialogue."""
    spec = ForgeIntakeEngine.process_forge_intake({"optimization_mode": "MIN_RELATIONAL_ALGEBRA"})
    assert spec.optimization_mode == "MIN_RELATIONAL_ALGEBRA"
    assert spec.target_environment == "local_duckdb"
    assert "predefined_gate" in spec.suites_enabled
