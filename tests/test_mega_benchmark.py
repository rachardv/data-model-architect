import pytest
from src.mega_benchmark import MegaBenchmarkRunner

def test_mega_benchmark_end_to_end():
    report = MegaBenchmarkRunner.run_mega_benchmark(total_cases=5, verbose=False, end_to_end=True)
    
    assert report["overall_status"] == "PASS"
    assert report["overall_accuracy_pct"] == 100.0
    assert report["total_cases_evaluated"] == 5
    assert report["cases_passed"] == 5
    assert report["mode"] == "END_TO_END_MODEL_GENERATION"
    assert "latency_metrics_ms" in report
    assert "domain_accuracy_matrix" in report
    
    # Verify physical pillars in sample cases
    sample = report["sample_cases"][0]
    assert "pillars" in sample
    assert sample["pillars"]["metric_conservation"] == "PASS"
    assert sample["pillars"]["temporal_causality"] == "PASS"
    assert sample["pillars"]["referential_integrity"] == "PASS"
    assert sample["pillars"]["query_execution"] == "PASS"
    assert sample["model_status"] == "CERTIFIED_PRODUCTION_READY"

def test_mega_benchmark_fast_nlp():
    report = MegaBenchmarkRunner.run_mega_benchmark(total_cases=25, verbose=False, end_to_end=False)
    
    assert report["overall_status"] == "PASS"
    assert report["overall_accuracy_pct"] == 100.0
    assert report["total_cases_evaluated"] == 25
    assert report["cases_passed"] == 25
    assert report["mode"] == "FAST_NLP_CLASSIFICATION"
    assert len(report["domain_accuracy_matrix"]) == 25

def test_mega_benchmark_export(tmp_path):
    export_file = str(tmp_path / "mega_results.json")
    report = MegaBenchmarkRunner.run_mega_benchmark(total_cases=5, export_path=export_file, verbose=False, end_to_end=True)
    
    import os
    import json
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["total_cases_evaluated"] == 5
    assert loaded["overall_accuracy_pct"] == 100.0
    assert loaded["mode"] == "END_TO_END_MODEL_GENERATION"
