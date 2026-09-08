import pytest
from src.forge import ForgeEngineRunner

def test_forge_engine_certification_suite():
    """Validates full execution of the Forge Workflow certification battery."""
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
