import pytest
from src.semantic_benchmarks import SemanticBenchmarkRunner

def test_semantic_benchmark_suite_execution():
    results = SemanticBenchmarkRunner.run_all_benchmarks()
    assert results["overall_status"] == "PASS"
    assert results["overall_score"] == 100.0
    assert results["scenarios_evaluated"] == 25
    assert results["scenarios_passed"] == 25
    
    # Check scenario details
    for sc in results["results"]:
        assert sc["status"] == "PASS"
        assert sc["classified_pattern"] == sc["expected_pattern"]
