import os
import pytest
from src.medallion_generator import MedallionPipelineGenerator
from src.orchestration.captain import CaptainOrchestrator

def test_bronze_layer_generation_with_sample_inserts():
    source_tables = [
        {
            "table_name": "customers",
            "columns": [
                {"name": "customer_id", "type": "VARCHAR(64)"},
                {"name": "customer_name", "type": "VARCHAR(255)"},
                {"name": "email", "type": "VARCHAR(255)"},
                {"name": "updated_at", "type": "TIMESTAMPTZ"}
            ]
        }
    ]
    bronze = MedallionPipelineGenerator.generate_bronze_layer("retail", source_tables, include_sample_data=True)
    assert "raw_retail_customers" in bronze
    sql = bronze["raw_retail_customers"]
    assert "CREATE TABLE raw_retail_customers" in sql
    assert "_raw_payload_id" in sql
    assert "_ingested_at" in sql
    assert "INSERT INTO raw_retail_customers" in sql
    assert "Alice Smith" in sql

def test_silver_layer_deduplication_and_quarantine_views():
    source_tables = [
        {
            "table_name": "orders",
            "columns": [
                {"name": "order_id", "type": "BIGINT"},
                {"name": "customer_id", "type": "VARCHAR(64)"},
                {"name": "total_amount", "type": "DECIMAL(14,2)"},
                {"name": "order_status", "type": "VARCHAR(32)"},
                {"name": "order_timestamp", "type": "TIMESTAMPTZ"}
            ]
        }
    ]
    target_schema = {
        "tables": [
            {
                "name": "fact_retail_orders",
                "type": "FACT",
                "columns": [{"name": "order_id", "type": "BIGINT"}]
            }
        ]
    }
    rules = [
        {"description": "Total amount non-negative", "definition": "total_amount >= 0.00"}
    ]
    silver = MedallionPipelineGenerator.generate_silver_layer(
        domain="retail",
        source_tables=source_tables,
        target_schema=target_schema,
        rules=rules,
        quality_policy="QUARANTINE_VIEW"
    )
    
    assert "stg_retail_orders" in silver
    assert "quarantine_retail_orders" in silver
    
    stg_sql = silver["stg_retail_orders"]
    assert "ROW_NUMBER() OVER" in stg_sql
    assert "total_amount >= 0.00" in stg_sql
    assert "order_sk" in stg_sql
    
    quarantine_sql = silver["quarantine_retail_orders"]
    assert "FAILED_INVARIANT: total_amount >= 0.00" in quarantine_sql
    assert "quarantined_at" in quarantine_sql

def test_gold_layer_scd2_merge_and_fact_load():
    target_schema = {
        "tables": [
            {
                "name": "dim_retail_customer_core",
                "type": "DIMENSION",
                "primary_key": "customer_sk",
                "columns": [
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "customer_id", "type": "VARCHAR(64)"},
                    {"name": "customer_name", "type": "VARCHAR(255)"},
                    {"name": "scd_valid_from", "type": "TIMESTAMPTZ"},
                    {"name": "scd_valid_to", "type": "TIMESTAMPTZ"}
                ]
            },
            {
                "name": "fact_retail_orders",
                "type": "FACT",
                "primary_key": "order_id",
                "columns": [
                    {"name": "order_id", "type": "BIGINT"},
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)"}
                ]
            }
        ]
    }
    gold = MedallionPipelineGenerator.generate_gold_layer("retail", target_schema, merge_strategy="ANSI_MERGE")
    
    assert "dim_retail_customer_core" in gold
    assert "fact_retail_orders" in gold
    
    dim_sql = gold["dim_retail_customer_core"]
    assert "MERGE INTO dim_retail_customer_core AS target" in dim_sql
    assert "scd_valid_to = '9999-12-31 23:59:59 UTC'" in dim_sql
    assert "v_current_dim_retail_customer_core" in dim_sql
    
    fact_sql = gold["fact_retail_orders"]
    assert "INSERT INTO fact_retail_orders" in fact_sql
    assert "LEFT JOIN v_current_dim_retail_customer_core" in fact_sql

def test_pipeline_file_export(tmp_path):
    pipeline = {
        "bronze": {"raw_retail_customers": "-- bronze sql"},
        "silver": {"stg_retail_customers": "-- silver sql"},
        "gold": {"dim_retail_customers": "-- gold sql"}
    }
    exported = MedallionPipelineGenerator.export_pipeline_files(str(tmp_path), "retail", pipeline)
    assert len(exported["bronze"]) == 1
    assert len(exported["silver"]) == 1
    assert len(exported["gold"]) == 1
    assert os.path.exists(exported["bronze"][0])
    assert os.path.exists(exported["silver"][0])
    assert os.path.exists(exported["gold"][0])

def test_captain_orchestrator_generates_and_exports_medallion(tmp_path):
    captain = CaptainOrchestrator(output_dir=str(tmp_path))
    payload = {
        "domain": "ecommerce",
        "branch": "NEW_MODEL",
        "narrative": "A customer places orders on our platform.",
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
    assert "medallion_pipeline" in result
    assert result["medallion_pipeline"]["total_sql_artifacts"] >= 4
    assert len(result["exported_pipeline_files"]["bronze"]) >= 1
    assert len(result["exported_pipeline_files"]["silver"]) >= 1
    assert len(result["exported_pipeline_files"]["gold"]) >= 1
