import pytest
from src.tpcdi_benchmark import TPCDIBenchmarkRunner

def test_tpcdi_full_benchmark_runner():
    """Verify official TPC-DI 3-batch lifecycle and 46 automated audit queries."""
    results = TPCDIBenchmarkRunner.run_full_benchmark()
    
    assert results["status"] == "PASS"
    assert results["score"] == 25
    assert results["total_batches"] == 3
    assert results["batches_executed"] == 3
    assert results["total_audits"] == 46
    assert results["audits_passed"] == 46
    assert results["metric_drift"] == 0.0000
    assert len(results["audit_details"]) == 46
    assert results["execution_time_ms"] > 0

def test_tpcdi_audit_sections_coverage():
    """Verify all 6 audit sections have 100% passing rate."""
    results = TPCDIBenchmarkRunner.run_full_benchmark()
    audit_details = results["audit_details"]
    
    for item in audit_details:
        assert item["status"] == "PASS", f"Audit {item['audit_id']}: {item['description']} failed"
        assert item["audit_id"] >= 1 and item["audit_id"] <= 46

def test_tpcdi_zero_metric_drift():
    """Verify trade amount and financial holdings reconciliation have exactly 0.0 drift."""
    results = TPCDIBenchmarkRunner.run_full_benchmark()
    assert results["metric_drift"] == 0.0000

    # Specifically check Audit 11 (Trade Volume) and Audit 12 (Trade Revenue)
    audit_map = {a["audit_id"]: a for a in results["audit_details"]}
    assert audit_map[11]["status"] == "PASS"
    assert audit_map[12]["status"] == "PASS"
    assert audit_map[13]["status"] == "PASS"

def test_tpcdi_scd2_and_point_in_time():
    """Verify SCD2 versioning and late-arriving point-in-time causality."""
    results = TPCDIBenchmarkRunner.run_full_benchmark()
    audit_map = {a["audit_id"]: a for a in results["audit_details"]}
    
    # Audit 21: Exactly 1 active version per customer
    assert audit_map[21]["status"] == "PASS"
    # Audit 22: High-water sentinel 9999-12-31 on current rows
    assert audit_map[22]["status"] == "PASS"
    # Audit 25: Late-arriving trade binds to historical version 1 (Seattle)
    assert audit_map[25]["status"] == "PASS"

def test_tpcdi_quarantine_isolation():
    """Verify corrupt records are captured in DImessages and zero leakage to gold."""
    results = TPCDIBenchmarkRunner.run_full_benchmark()
    audit_map = {a["audit_id"]: a for a in results["audit_details"]}
    
    # Audit 44: DImessages covers all 3 batches
    assert audit_map[44]["status"] == "PASS"
    # Audit 45: Exactly 2 rejected records logged
    assert audit_map[45]["status"] == "PASS"
    # Audit 46: Zero quarantine leakage in FactTrade
    assert audit_map[46]["status"] == "PASS"
