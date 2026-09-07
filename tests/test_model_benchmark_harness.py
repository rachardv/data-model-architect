import pytest
import duckdb
from src.benchmark_harness import ModelBenchmarkHarness
from src.medallion_generator import MedallionPipelineGenerator
from src.orchestration.captain import CaptainOrchestrator

@pytest.fixture
def standard_retail_setup():
    domain = "retail_bench"
    target_schema = {
        "tables": [
            {
                "name": f"dim_{domain}_customer_core",
                "type": "DIMENSION",
                "primary_key": "customer_sk",
                "columns": [
                    {"name": "customer_sk", "type": "VARCHAR(64)"},
                    {"name": "customer_id", "type": "VARCHAR(64)"},
                    {"name": "customer_name", "type": "VARCHAR(255)"},
                    {"name": "scd_valid_from", "type": "TIMESTAMPTZ"},
                    {"name": "scd_valid_to", "type": "TIMESTAMPTZ"}
                ]
            },
            {
                "name": f"fact_{domain}_orders",
                "type": "FACT",
                "primary_key": "order_id",
                "columns": [
                    {"name": "order_id", "type": "BIGINT"},
                    {"name": "customer_sk", "type": "VARCHAR(64)"},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)"}
                ]
            }
        ]
    }
    pipeline = MedallionPipelineGenerator.generate_full_pipeline(
        domain=domain,
        source_tables=None,
        target_schema=target_schema
    )
    return domain, target_schema, pipeline

def test_clean_model_passes_all_four_pillars(standard_retail_setup):
    domain, target_schema, pipeline = standard_retail_setup
    scorecard = ModelBenchmarkHarness.run_full_benchmark(
        domain=domain,
        target_schema=target_schema,
        medallion_pipeline=pipeline
    )
    
    assert scorecard["overall_status"] == "PASS"
    assert scorecard["overall_score"] == 100.0
    assert scorecard["metric_conservation"]["status"] == "PASS"
    assert scorecard["temporal_causality"]["status"] == "PASS"
    assert scorecard["referential_integrity"]["status"] == "PASS"
    assert scorecard["query_execution"]["status"] == "PASS"
    assert scorecard["execution_time_ms"] > 0.0

def test_metric_inflation_detection():
    con = duckdb.connect(":memory:")
    scorecard = {"metric_conservation": {}}
    target_schema = {
        "tables": [
            {"name": "fact_sales", "type": "FACT"}
        ]
    }
    
    # Create raw table and an artificially inflated fact table (e.g. Cartesian 3x)
    con.execute("""
        CREATE TABLE raw_store_orders (total_amount DECIMAL(14,2));
        INSERT INTO raw_store_orders VALUES (100.00), (200.00); -- Total = $300.00
        
        CREATE TABLE fact_sales (total_amount_usd DECIMAL(14,2));
        INSERT INTO fact_sales VALUES (100.00), (100.00), (200.00), (200.00), (300.00); -- Total = $900.00 (3x inflation)
    """)
    
    ModelBenchmarkHarness._test_metric_conservation(con, "store", target_schema, scorecard)
    assert scorecard["metric_conservation"]["status"] == "FAIL"
    assert scorecard["metric_conservation"]["score"] == 0
    assert "Fan-out inflation detected" in scorecard["metric_conservation"]["details"]
    con.close()

def test_referential_integrity_catches_duplicate_pks():
    con = duckdb.connect(":memory:")
    scorecard = {"referential_integrity": {}}
    target_schema = {
        "tables": [
            {"name": "dim_product", "type": "DIMENSION", "primary_key": "product_sk"}
        ]
    }
    
    # Create table with duplicate PKs
    con.execute("""
        CREATE TABLE dim_product (product_sk BIGINT, product_name VARCHAR(64));
        INSERT INTO dim_product VALUES (1, 'Widget A'), (1, 'Widget A Duplicate');
    """)
    
    runner_res = {"quarantine_records_isolated": 0}
    ModelBenchmarkHarness._test_referential_integrity(con, target_schema, runner_res, scorecard)
    assert scorecard["referential_integrity"]["status"] == "FAIL"
    assert "Duplicate primary keys detected" in scorecard["referential_integrity"]["details"]
    con.close()

def test_captain_attaches_benchmark_scorecard():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "benchmarked_ecommerce",
        "branch": "NEW_MODEL",
        "narrative": "A customer purchases items online.",
        "usage_params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        }
    }
    
    result = captain.execute_workflow(payload)
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert "benchmark_scorecard" in result
    
    sc = result["benchmark_scorecard"]
    assert sc["overall_score"] == 100.0
    assert sc["overall_status"] == "PASS"
    assert sc["metric_conservation"]["status"] == "PASS"
    assert sc["temporal_causality"]["status"] == "PASS"
