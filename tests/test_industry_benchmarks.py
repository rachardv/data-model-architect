import pytest
from src.industry_benchmarks import IndustryBenchmarkRunner

def test_industry_benchmark_suite_execution():
    results = IndustryBenchmarkRunner.run_all_benchmarks(domain="retail")
    assert results["overall_status"] == "PASS"
    assert results["overall_score"] == 100.0
    
    # 1. SSB (Star Schema Benchmark)
    assert results["ssb"]["status"] == "PASS"
    assert results["ssb"]["score"] == 25
    assert "Star Schema Benchmark (SSB)" in results["ssb"]["details"]
    
    # 2. TPC-DS (Multi-Channel Retail)
    assert results["tpcds"]["status"] == "PASS"
    assert results["tpcds"]["score"] == 25
    assert "TPC-DS" in results["tpcds"]["details"]
    
    # 3. TPC-DI (ETL & Integration)
    assert results["tpcdi"]["status"] == "PASS"
    assert results["tpcdi"]["score"] == 25
    assert "TPC-DI" in results["tpcdi"]["details"]
    
    # 4. TPC-H (Decision Support Fan-out & Discounts)
    assert results["tpch"]["status"] == "PASS"
    assert results["tpch"]["score"] == 25
    assert "TPC-H" in results["tpch"]["details"]
