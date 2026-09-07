import pytest
import os
import tempfile
from src.dbt_generator import DBTProjectGenerator
from src.orchestration.captain import CaptainOrchestrator

@pytest.fixture
def sample_schema():
    return {
        "tables": [
            {
                "name": "dim_retail_customer_core",
                "type": "DIMENSION",
                "columns": [
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "customer_id", "type": "VARCHAR(64)"},
                    {"name": "customer_name", "type": "VARCHAR(255)"},
                    {"name": "email", "type": "VARCHAR(255)"},
                    {"name": "scd_valid_from", "type": "TIMESTAMPTZ"},
                    {"name": "scd_valid_to", "type": "TIMESTAMPTZ"},
                    {"name": "is_current", "type": "BOOLEAN"}
                ],
                "primary_key": "customer_sk"
            },
            {
                "name": "fact_retail_orders",
                "type": "FACT",
                "columns": [
                    {"name": "order_id", "type": "BIGINT"},
                    {"name": "customer_sk", "type": "BIGINT"},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)"},
                    {"name": "order_timestamp", "type": "TIMESTAMPTZ"}
                ],
                "primary_key": "order_id"
            }
        ]
    }

@pytest.fixture
def sample_sources():
    return [
        {
            "table_name": "customers",
            "columns": [
                {"name": "customer_id", "type": "VARCHAR(64)"},
                {"name": "customer_name", "type": "VARCHAR(255)"},
                {"name": "email", "type": "VARCHAR(255)"},
                {"name": "updated_at", "type": "TIMESTAMPTZ"}
            ]
        },
        {
            "table_name": "orders",
            "columns": [
                {"name": "order_id", "type": "BIGINT"},
                {"name": "customer_id", "type": "VARCHAR(64)"},
                {"name": "total_amount", "type": "DECIMAL(14,2)"},
                {"name": "order_timestamp", "type": "TIMESTAMPTZ"}
            ]
        }
    ]

def test_dbt_project_yaml_generation():
    yaml_content = DBTProjectGenerator.generate_dbt_project_yaml("retail")
    assert "name: 'data_model_retail'" in yaml_content
    assert "profile: 'default'" in yaml_content
    assert "+materialized: view" in yaml_content
    assert "+materialized: table" in yaml_content
    assert "model-paths:" in yaml_content

def test_dbt_sources_and_staging_models(sample_sources):
    sources_yaml = DBTProjectGenerator.generate_sources_yaml("retail", sample_sources)
    assert "name: raw" in sources_yaml
    assert "schema: raw_retail" in sources_yaml
    assert "- name: customers" in sources_yaml
    assert "- name: orders" in sources_yaml

    staging_models = DBTProjectGenerator.generate_staging_models("retail", sample_sources)
    assert "stg_retail_customers" in staging_models
    assert "stg_retail_orders" in staging_models
    
    cust_sql = staging_models["stg_retail_customers"]
    assert "{{ source('raw', 'customers') }}" in cust_sql
    assert "TRIM(customer_name) AS customer_name" in cust_sql
    assert "CAST(updated_at AS TIMESTAMPTZ) AS updated_at" in cust_sql

def test_dbt_marts_models_generation(sample_schema):
    marts = DBTProjectGenerator.generate_marts_models("retail", sample_schema)
    assert "dim_retail_customer_core" in marts
    assert "fact_retail_orders" in marts
    
    dim_sql = marts["dim_retail_customer_core"]
    assert "{{ ref('stg_retail_customers') }}" in dim_sql
    assert "ROW_NUMBER() OVER" in dim_sql
    
    fact_sql = marts["fact_retail_orders"]
    assert "{{ ref('stg_retail_orders') }}" in fact_sql
    assert "{{ ref('dim_retail_customer_core') }}" in fact_sql
    assert "COALESCE(c.customer_sk, -1) AS customer_sk" in fact_sql

def test_dbt_schema_tests_generation(sample_schema):
    tests_yaml = DBTProjectGenerator.generate_schema_tests_yaml("retail", sample_schema)
    assert "- name: dim_retail_customer_core" in tests_yaml
    assert "- name: fact_retail_orders" in tests_yaml
    
    # Primary keys must have unique and not_null
    assert "unique" in tests_yaml
    assert "not_null" in tests_yaml
    
    # Foreign keys must have relationships test
    assert "relationships:" in tests_yaml
    assert "to: ref('dim_retail_customer_core')" in tests_yaml
    assert "field: customer_sk" in tests_yaml

def test_dbt_export_directory_structure(sample_schema, sample_sources, tmp_path):
    project_data = DBTProjectGenerator.generate_dbt_project("retail", sample_schema, sample_sources)
    exported = DBTProjectGenerator.export_dbt_project(str(tmp_path), "retail", project_data)
    
    assert len(exported["config"]) == 2
    for p in exported["config"]:
        assert os.path.exists(p)
    assert any("packages.yml" in p for p in exported["config"])
    assert any("dbt_project.yml" in p for p in exported["config"])
    
    assert len(exported["staging"]) >= 2
    for p in exported["staging"]:
        assert os.path.exists(p)
        
    assert len(exported["marts"]) >= 2
    for p in exported["marts"]:
        assert os.path.exists(p)
        
    assert len(exported["tests"]) == 1
    assert os.path.exists(exported["tests"][0])

def test_captain_orchestrator_exports_dbt():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "ecommerce_dbt",
        "branch": "NEW_MODEL",
        "narrative": "A customer places orders online on our e-commerce platform.",
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
    assert "dbt_project" in result
    assert result["dbt_project"]["total_models"] >= 3
    assert "exported_dbt_files" in result
    assert len(result["exported_dbt_files"]["staging"]) >= 1
    assert len(result["exported_dbt_files"]["marts"]) >= 1
