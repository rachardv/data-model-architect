import os
import json
import pytest
import tempfile
from src.benchmark_catalog import (
    PredefinedBenchmarkCase,
    VerificationQuery,
    get_predefined_benchmark_catalog,
    register_benchmark_case,
    clear_registered_benchmark_cases
)
from src.decision_tracer import DecisionTracer
from src.predefined_benchmark_gate import PredefinedBenchmarkGate

@pytest.fixture(autouse=True)
def clean_catalog():
    """Ensure catalog starts and ends clean for each test."""
    clear_registered_benchmark_cases()
    yield
    clear_registered_benchmark_cases()

def test_catalog_empty_by_default():
    """Validates that the default catalog is empty per user directive."""
    cases = get_predefined_benchmark_catalog()
    assert isinstance(cases, list)
    assert len(cases) == 0

def test_run_all_cases_empty_catalog():
    """Validates graceful execution when the catalog contains zero cases."""
    gate = PredefinedBenchmarkGate()
    scorecard = gate.run_all_cases()
    assert scorecard["status"] == "EMPTY_CATALOG"
    assert scorecard["total_cases"] == 0
    assert scorecard["passed_cases"] == 0
    assert "empty" in scorecard["message"].lower()

def test_decision_tracer_persistence_and_overwrite():
    """Validates that DecisionTracer cleanly writes and overwrites traces on disk."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracer1 = DecisionTracer(
            case_id="TEST-01",
            domain="retail",
            name="Sample Test Case",
            hazard_category="CLEAN_BASELINE",
            is_intentional_trap=False,
            prompt="A retail customer places orders.",
            expected_status="CERTIFIED_PRODUCTION_READY"
        )
        tracer1.record_intake({"status": "PASS", "completeness_score": 100.0})
        tracer1.record_architecture({"architecture_pattern": "KIMBALL_STAR_SCD2"})
        tracer1.record_query_verification(
            name="Test Query",
            query="SELECT 1;",
            assertion_type="scalar_eq",
            expected_value=1,
            actual_value=1,
            passed=True,
            latency_ms=1.5
        )
        tracer1.finalize("CERTIFIED_PRODUCTION_READY")
        paths1 = tracer1.save(trace_dir=tmp_dir)

        assert os.path.exists(paths1["json_path"])
        assert os.path.exists(paths1["md_path"])

        with open(paths1["json_path"], "r", encoding="utf-8") as f:
            data1 = json.load(f)
        assert data1["verdict"] == "PASS"
        assert data1["case_id"] == "TEST-01"

        # Overwrite run
        tracer2 = DecisionTracer(
            case_id="TEST-01",
            domain="retail",
            name="Sample Test Case Redeployed",
            hazard_category="CLEAN_BASELINE",
            is_intentional_trap=False,
            prompt="A retail customer places orders redeployed.",
            expected_status="CERTIFIED_PRODUCTION_READY"
        )
        tracer2.record_intake({"status": "PASS", "completeness_score": 100.0})
        tracer2.record_architecture({"architecture_pattern": "KIMBALL_STAR_SCD2"})
        tracer2.finalize("CERTIFIED_PRODUCTION_READY")
        paths2 = tracer2.save(trace_dir=tmp_dir)

        assert paths1["json_path"] == paths2["json_path"]
        with open(paths2["json_path"], "r", encoding="utf-8") as f:
            data2 = json.load(f)
        assert data2["name"] == "Sample Test Case Redeployed"

def test_single_case_execution_in_duckdb():
    """Validates 1-by-1 execution of a registered benchmark case with DuckDB verification queries."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        sample_case = PredefinedBenchmarkCase(
            case_id="CASE-UNIT-01",
            domain="retail",
            name="Unit Retail Case",
            description="Tests standard retail dimensional model execution in DuckDB.",
            hazard_category="CLEAN_BASELINE",
            is_intentional_trap=False,
            prompt="We operate a retail store where customers place orders with total sales amounts.",
            business_answers=[
                "Core business processes: retail merchandise orders",
                "Grain: One record per order",
                "Dimensions: Customers with SCD2 tracking",
                "Metrics: total_amount_usd, estimated_delivery_days"
            ],
            expected_status="CERTIFIED_PRODUCTION_READY",
            verification_queries=[
                VerificationQuery(
                    name="Customer Core Table Check",
                    query="SELECT COUNT(*) FROM dim_retail_customer_core WHERE is_current = true;",
                    assertion_type="scalar_gt",
                    expected_value=0,
                    failure_message="Expected active customer records"
                ),
                VerificationQuery(
                    name="Orders Fact Grain Check",
                    query="SELECT COUNT(*) FROM fact_retail_orders WHERE total_amount_usd >= 0;",
                    assertion_type="scalar_gt",
                    expected_value=0,
                    failure_message="Expected positive fact rows"
                )
            ]
        )

        register_benchmark_case(sample_case)
        assert len(get_predefined_benchmark_catalog()) == 1

        gate = PredefinedBenchmarkGate(trace_dir=tmp_dir, output_dir=tmp_dir)
        res = gate.run_case(sample_case)

        assert res["case_id"] == "CASE-UNIT-01"
        assert res["verdict"] == "PASS"
        assert res["final_status"] == "CERTIFIED_PRODUCTION_READY"
        assert res["queries_executed"] == 2
        assert res["queries_passed"] == 2
        assert os.path.exists(res["trace_files"]["json_path"])
        assert os.path.exists(res["trace_files"]["md_path"])

def test_intentional_trap_defense_halt():
    """Validates that intentional traps (e.g. contradiction) correctly verify defense halts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        trap_case = PredefinedBenchmarkCase(
            case_id="TRAP-01",
            domain="highfreq",
            name="Contradiction Guardrail Trap",
            description="Intentional Trap testing Gate 0 conflict detection.",
            hazard_category="CONTRADICTION_HALT",
            is_intentional_trap=True,
            rules=[
                {
                    "description": "Multi-year analytical reporting and 10-year trend analysis over a billion row dataset",
                    "enforcement": "Hard Database CHECK",
                    "definition": "row_count >= 1000000000"
                }
            ],
            baseline_vectors={
                "workload_intent": "OLTP"
            },
            expected_status="AWAITING_ARCHITECTURAL_CONFIRMATION",
            prompt="Financial trading desk requiring sub-millisecond row locks for live OLTP transactions.",
            business_answers=[
                "Processes: high frequency order execution and reporting",
                "Grain: One record per tick transaction",
                "Dimensions: Instrument and Trader",
                "Metrics: tick_price, volume"
            ],
            verification_queries=[]
        )

        gate = PredefinedBenchmarkGate(trace_dir=tmp_dir, output_dir=tmp_dir)
        res = gate.run_case(trap_case)

        assert res["case_id"] == "TRAP-01"
        assert res["is_intentional_trap"] is True
        assert res["final_status"] == "AWAITING_ARCHITECTURAL_CONFIRMATION"
        assert res["verdict"] == "PASS"  # Pass because it successfully triggered the intended defense halt!
