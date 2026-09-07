import pytest
from src.mega_benchmark import MegaBenchmarkRunner

def test_mega_benchmark_evaluation():
    report = MegaBenchmarkRunner.run_mega_benchmark(total_cases=50, verbose=False)
    
    assert report["overall_status"] == "PASS"
    assert report["overall_accuracy_pct"] == 100.0
    assert report["total_cases_evaluated"] == 50
    assert report["cases_passed"] == 50
    assert report["cases_failed"] == 0
    assert report["throughput_cases_per_sec"] > 0.0
    assert "latency_metrics_ms" in report
    assert "domain_accuracy_matrix" in report
    assert len(report["domain_accuracy_matrix"]) == 25

def test_mega_benchmark_export(tmp_path):
    export_file = str(tmp_path / "mega_results.json")
    report = MegaBenchmarkRunner.run_mega_benchmark(total_cases=25, export_path=export_file, verbose=False)
    
    import os
    import json
    assert os.path.exists(export_file)
    with open(export_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["total_cases_evaluated"] == 25
    assert loaded["overall_accuracy_pct"] == 100.0
