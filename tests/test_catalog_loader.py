import os
import json
import pytest
import tempfile
import duckdb
from forge.benchmark_catalog import (
    PredefinedBenchmarkCase,
    VerificationQuery,
    get_predefined_benchmark_catalog,
    clear_registered_benchmark_cases
)
from forge.catalog_loader import BenchmarkCatalogLoader
from forge.predefined_benchmark_gate import PredefinedBenchmarkGate

@pytest.fixture(autouse=True)
def clean_catalog():
    """Ensure catalog starts and ends clean for each test."""
    clear_registered_benchmark_cases()
    yield
    clear_registered_benchmark_cases()

def test_load_single_case_yaml():
    """Validates loading a single YAML benchmark case from disk."""
    case_path = os.path.join("benchmarks", "catalog", "curated", "CASE_01_retail_kimball_star.yaml")
    assert os.path.exists(case_path), f"Expected reference case to exist at {case_path}"
    
    case = BenchmarkCatalogLoader.load_case_file(case_path)
    assert isinstance(case, PredefinedBenchmarkCase)
    assert case.case_id == "CASE-01"
    assert case.domain == "retail"
    assert case.hazard_category == "CLEAN_BASELINE"
    assert case.is_intentional_trap is False
    assert "curated" in case.tags
    assert "retail" in case.tags
    assert len(case.verification_queries) == 3
    assert case.source_file is not None

def test_load_single_case_json():
    """Validates loading a single JSON benchmark case from disk."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        json_path = os.path.join(tmp_dir, "test_case.json")
        data = {
            "case_id": "CASE-JSON-01",
            "domain": "finance",
            "name": "JSON Finance Case",
            "description": "Validates JSON specification loading",
            "hazard_category": "CLEAN_BASELINE",
            "is_intentional_trap": False,
            "prompt": "Corporate finance ledger tracking journal entries.",
            "expected_status": "CERTIFIED_PRODUCTION_READY",
            "tags": ["curated", "finance"],
            "verification_queries": []
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        case = BenchmarkCatalogLoader.load_case_file(json_path)
        assert case.case_id == "CASE-JSON-01"
        assert case.domain == "finance"
        assert "finance" in case.tags

def test_load_from_directory_auto_discovery():
    """Validates recursive auto-discovery of all benchmark cases in benchmarks/catalog."""
    cases = BenchmarkCatalogLoader.load_from_directory("benchmarks/catalog", register=True, clear_existing=True)
    assert len(cases) >= 2
    case_ids = {c.case_id for c in cases}
    assert "CASE-01" in case_ids
    assert "TRAP-01" in case_ids

    # Verify registered in global catalog
    registered = get_predefined_benchmark_catalog()
    assert len(registered) == len(cases)

def test_invalid_case_schema_raises_error():
    """Validates that malformed benchmark specifications raise diagnostic validation errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        bad_path = os.path.join(tmp_dir, "bad_case.yaml")
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("domain: retail\n# Missing mandatory case_id, name, hazard_category, prompt\n")

        with pytest.raises(ValueError) as exc_info:
            BenchmarkCatalogLoader.load_case_file(bad_path)
        assert "validation error" in str(exc_info.value).lower()

def test_filter_cases_by_tag_and_hazard():
    """Validates filtering benchmark cases by tags, hazard categories, and IDs."""
    cases = BenchmarkCatalogLoader.load_from_directory("benchmarks/catalog", register=False)
    
    # Filter by tag
    retail_cases = BenchmarkCatalogLoader.filter_cases(cases, tags=["retail"])
    assert len(retail_cases) >= 1
    assert all("retail" in c.tags for c in retail_cases)

    # Filter by trap tag
    trap_cases = BenchmarkCatalogLoader.filter_cases(cases, tags=["trap"])
    assert len(trap_cases) >= 1
    assert all(c.is_intentional_trap for c in trap_cases)

    # Filter by hazard category
    contradiction_cases = BenchmarkCatalogLoader.filter_cases(cases, hazard_category="CONTRADICTION_HALT")
    assert len(contradiction_cases) >= 1
    assert contradiction_cases[0].case_id == "TRAP-01"

def test_seed_sql_injection_in_duckdb():
    """Validates that seed_sql executes in DuckDB and verification queries can assert on seeded tables."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        case = PredefinedBenchmarkCase(
            case_id="SEED-SQL-01",
            domain="retail",
            name="Seed SQL Test Case",
            description="Tests raw seed_sql injection into DuckDB",
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
            seed_sql="CREATE TABLE seed_pallets (pallet_id INT, weight_kg DOUBLE); INSERT INTO seed_pallets VALUES (101, 450.5), (102, 320.0);",
            verification_queries=[
                VerificationQuery(
                    name="Seeded Pallets Count",
                    query="SELECT COUNT(*) FROM seed_pallets;",
                    assertion_type="scalar_eq",
                    expected_value=2,
                    failure_message="Expected 2 seeded pallets"
                ),
                VerificationQuery(
                    name="Total Weight Sum",
                    query="SELECT SUM(weight_kg) FROM seed_pallets;",
                    assertion_type="scalar_eq",
                    expected_value=770.5,
                    failure_message="Expected exact weight sum"
                )
            ]
        )
        gate = PredefinedBenchmarkGate(trace_dir=tmp_dir, output_dir=tmp_dir)
        res = gate.run_case(case)
        assert res["verdict"] == "PASS"
        assert res["queries_passed"] == 2

def test_seed_data_inline_dict_injection_in_duckdb():
    """Validates that seed_data (inline dict mapping table -> rows) inserts records into DuckDB."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        case = PredefinedBenchmarkCase(
            case_id="SEED-DATA-01",
            domain="retail",
            name="Seed Data Inline Dict Case",
            description="Tests inline dictionary records seed injection into DuckDB",
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
            seed_data={
                "seed_transactions": [
                    {"tx_id": "TX-01", "amount": 100.0, "status": "APPROVED"},
                    {"tx_id": "TX-02", "amount": 250.5, "status": "APPROVED"},
                    {"tx_id": "TX-03", "amount": 50.0, "status": "DECLINED"}
                ]
            },
            verification_queries=[
                VerificationQuery(
                    name="Approved Transactions Sum",
                    query="SELECT SUM(amount) FROM seed_transactions WHERE status = 'APPROVED';",
                    assertion_type="scalar_eq",
                    expected_value=350.5,
                    failure_message="Expected approved transaction amount sum"
                )
            ]
        )
        gate = PredefinedBenchmarkGate(trace_dir=tmp_dir, output_dir=tmp_dir)
        res = gate.run_case(case)
        assert res["verdict"] == "PASS"
        assert res["queries_passed"] == 1

def test_list_catalog_summary():
    """Validates generating summary dictionaries for discovered cases."""
    BenchmarkCatalogLoader.load_from_directory("benchmarks/catalog", register=True)
    summaries = BenchmarkCatalogLoader.list_catalog_summary()
    assert len(summaries) >= 2
    for s in summaries:
        assert "case_id" in s
        assert "name" in s
        assert "hazard_category" in s
        assert "query_count" in s
