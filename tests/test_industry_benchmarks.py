import pytest
from src.industry_benchmarks import IndustryBenchmarkRunner

def test_industry_benchmark_suite_execution():
    results = IndustryBenchmarkRunner.run_all_benchmarks(domain="retail")
    assert results["overall_status"] == "PASS"
    assert results["overall_score"] == 100.0
    
    # 1. SSB (Star Schema Benchmark - 13 queries)
    assert results["ssb"]["status"] == "PASS"
    assert results["ssb"]["score"] == 25
    assert results["ssb"]["queries_executed"] == 13
    assert results["ssb"]["queries_passed"] == 13
    assert "Star Schema Benchmark (SSB)" in results["ssb"]["details"]
    
    # 2. TPC-DS (Multi-Channel Retail - 99 queries)
    assert results["tpcds"]["status"] == "PASS"
    assert results["tpcds"]["score"] == 25
    assert results["tpcds"]["queries_executed"] == 99
    assert results["tpcds"]["queries_passed"] >= 90
    assert "TPC-DS" in results["tpcds"]["details"]
    
    # 3. TPC-DI (ETL & Integration - 18 scenarios)
    assert results["tpcdi"]["status"] == "PASS"
    assert results["tpcdi"]["score"] == 25
    assert results["tpcdi"]["scenarios_executed"] == 18
    assert results["tpcdi"]["scenarios_passed"] == 18
    assert "TPC-DI" in results["tpcdi"]["details"]
    
    # 4. TPC-H (Decision Support Fan-out & Discounts - 22 queries)
    assert results["tpch"]["status"] == "PASS"
    assert results["tpch"]["score"] == 25
    assert results["tpch"]["queries_executed"] == 22
    assert results["tpch"]["queries_passed"] == 22
    assert "TPC-H" in results["tpch"]["details"]

    assert results["total_test_cases_executed"] >= 150
