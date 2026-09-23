import os
import json
import pytest
import tempfile
from decimal import Decimal
from forge.snapshot_engine import GoldenSnapshotEngine, _normalize_json_val

@pytest.fixture
def sample_case_results():
    return [
        {
            "case_id": "CASE-01",
            "name": "Retail Mart",
            "domain": "retail",
            "hazard_category": "CLEAN_BASELINE",
            "is_intentional_trap": False,
            "expected_status": "CERTIFIED_PRODUCTION_READY",
            "final_status": "CERTIFIED_PRODUCTION_READY",
            "verdict": "PASS",
            "execution_time_ms": 120.5,
            "schema_decisions": [
                {
                    "table_name": "dim_retail_customer",
                    "type": "DIMENSION",
                    "primary_key": "customer_sk",
                    "columns": ["customer_sk", "customer_name", "is_current"]
                },
                {
                    "table_name": "fact_retail_orders",
                    "type": "FACT",
                    "primary_key": "order_id",
                    "columns": ["order_id", "customer_sk", "total_amount_usd"]
                }
            ],
            "queries_trace": [
                {
                    "name": "Customer Active Records",
                    "assertion_type": "scalar_gt",
                    "expected_value": 0,
                    "actual_value": 2,
                    "passed": True,
                    "latency_ms": 0.45
                },
                {
                    "name": "Revenue Sum",
                    "assertion_type": "scalar_gt",
                    "expected_value": 0.0,
                    "actual_value": Decimal("385.00"),
                    "passed": True,
                    "latency_ms": 0.50
                }
            ]
        },
        {
            "case_id": "TRAP-01",
            "name": "Contradiction Trap",
            "domain": "trading",
            "hazard_category": "CONTRADICTORY_WORKLOAD",
            "is_intentional_trap": True,
            "expected_status": "CRITICAL_RISK_HALT",
            "final_status": "CRITICAL_RISK_HALT",
            "verdict": "PASS",
            "execution_time_ms": 8.5,
            "schema_decisions": [],
            "queries_trace": []
        }
    ]

def test_normalize_json_val():
    assert _normalize_json_val(Decimal("100.5")) == 100.5
    assert _normalize_json_val(Decimal("100.0")) == 100
    assert _normalize_json_val({"a": Decimal("25.2"), "b": [Decimal("10.0")]}) == {"a": 25.2, "b": [10]}
    assert _normalize_json_val("plain_string") == "plain_string"

def test_capture_and_load_snapshot(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        payload = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        assert os.path.exists(snap_path)
        assert payload["total_cases"] == 2
        assert "CASE-01" in payload["cases"]
        assert "TRAP-01" in payload["cases"]

        # Verify Decimal normalization in saved file
        with open(snap_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        assert raw["cases"]["CASE-01"]["queries"][1]["actual_value"] == 385.0

        loaded = GoldenSnapshotEngine.load_snapshot(snap_path)
        assert loaded is not None
        assert loaded["total_cases"] == 2

def test_load_nonexistent_snapshot():
    assert GoldenSnapshotEngine.load_snapshot("/non/existent/path.json") is None

def test_compare_run_to_snapshot_identical(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        baseline = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        diff = GoldenSnapshotEngine.compare_run_to_snapshot(sample_case_results, baseline)
        assert diff["verdict"] == "IDENTICAL"
        assert not diff["has_drift"]
        assert not diff["has_schema_drift"]
        assert not diff["has_status_drift"]
        assert not diff["has_latency_regression"]
        assert diff["clean_cases_count"] == 2
        assert diff["drifted_cases_count"] == 0

        report = GoldenSnapshotEngine.format_diff_terminal_report(diff)
        assert "100% IDENTICAL" in report
        assert "[CLEAN]" in report

def test_compare_run_schema_drift_table_added_and_removed(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        baseline = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        # Mutate live run: remove fact_retail_orders, add fact_inventory
        modified = [
            {
                **sample_case_results[0],
                "schema_decisions": [
                    {
                        "table_name": "dim_retail_customer",
                        "type": "DIMENSION",
                        "primary_key": "customer_sk",
                        "columns": ["customer_sk", "customer_name", "is_current"]
                    },
                    {
                        "table_name": "fact_inventory",
                        "type": "FACT",
                        "primary_key": "inventory_id",
                        "columns": ["inventory_id", "stock_count"]
                    }
                ]
            },
            sample_case_results[1]
        ]

        diff = GoldenSnapshotEngine.compare_run_to_snapshot(modified, baseline)
        assert diff["verdict"] == "DRIFT_DETECTED"
        assert diff["has_drift"]
        assert diff["has_schema_drift"]
        assert diff["drifted_cases_count"] == 1
        
        c0 = diff["cases"][0]
        assert c0["schema_drift"]
        assert any("fact_retail_orders" in d for d in c0["details"])
        assert any("fact_inventory" in d for d in c0["details"])

def test_compare_run_schema_drift_column_change_and_pk(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        baseline = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        # Mutate columns and PK of dim_retail_customer
        modified = [
            {
                **sample_case_results[0],
                "schema_decisions": [
                    {
                        "table_name": "dim_retail_customer",
                        "type": "DIMENSION",
                        "primary_key": "customer_alt_id",  # PK change
                        "columns": ["customer_sk", "customer_name", "phone_number"] # dropped is_current, added phone_number
                    },
                    sample_case_results[0]["schema_decisions"][1]
                ]
            },
            sample_case_results[1]
        ]

        diff = GoldenSnapshotEngine.compare_run_to_snapshot(modified, baseline)
        assert diff["verdict"] == "DRIFT_DETECTED"
        assert diff["has_schema_drift"]
        c0 = diff["cases"][0]
        assert any("is_current" in d for d in c0["details"])
        assert any("phone_number" in d for d in c0["details"])
        assert any("PK changed" in d for d in c0["details"])

def test_compare_run_status_deviation(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        baseline = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        # Mutate TRAP-01 to fail defense
        modified = [
            sample_case_results[0],
            {
                **sample_case_results[1],
                "final_status": "CERTIFIED_PRODUCTION_READY",
                "verdict": "FAIL"
            }
        ]

        diff = GoldenSnapshotEngine.compare_run_to_snapshot(modified, baseline)
        assert diff["verdict"] == "DRIFT_DETECTED"
        assert diff["has_status_drift"]
        c1 = diff["cases"][1]
        assert not c1["status_match"]
        assert not c1["verdict_match"]

def test_compare_run_latency_regression(sample_case_results):
    with tempfile.TemporaryDirectory() as tmpdir:
        snap_path = os.path.join(tmpdir, "test_snapshot.json")
        baseline = GoldenSnapshotEngine.capture_snapshot(sample_case_results, snap_path)

        # Latency spike in query 0: from 0.45ms to 5.0ms (+1011%, delta 4.55ms)
        modified = [
            {
                **sample_case_results[0],
                "queries_trace": [
                    {
                        **sample_case_results[0]["queries_trace"][0],
                        "latency_ms": 5.00
                    },
                    sample_case_results[0]["queries_trace"][1]
                ]
            },
            sample_case_results[1]
        ]

        diff = GoldenSnapshotEngine.compare_run_to_snapshot(
            modified, baseline, latency_threshold_pct=100.0, min_latency_delta_ms=1.0
        )
        assert diff["verdict"] == "PERF_ALERT"
        assert not diff["has_drift"]
        assert diff["has_latency_regression"]
        assert diff["perf_alert_cases_count"] == 1
        
        report = GoldenSnapshotEngine.format_diff_terminal_report(diff)
        assert "[PERF ALERT]" in report
        assert "latency spike" in report
