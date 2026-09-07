import pytest
from src.dbt_generator import DBTProjectGenerator
from src.dbt_evaluator import DBTProjectEvaluator

def test_dbt_project_evaluator_clean_project():
    # Build clean project
    target_schema = {
        "tables": [
            {
                "name": "dim_customer",
                "type": "DIMENSION",
                "primary_key": "customer_sk",
                "columns": [
                    {"name": "customer_sk", "type": "VARCHAR(64)"},
                    {"name": "customer_id", "type": "VARCHAR(64)"},
                    {"name": "customer_name", "type": "VARCHAR(255)"}
                ]
            },
            {
                "name": "fact_orders",
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
    project = DBTProjectGenerator.generate_dbt_project(
        domain="retail",
        target_schema=target_schema
    )
    
    # Assert packages.yml is populated
    assert "packages_yaml" in project
    assert "dbt-labs/dbt_project_evaluator" in project["packages_yaml"]
    
    # Evaluate project
    eval_res = DBTProjectEvaluator.evaluate_project(project)
    assert eval_res["status"] == "PASS"
    assert eval_res["total_rules"] == 4
    assert eval_res["rules_passed"] == 4
    assert len(eval_res["violations"]) == 0
    assert eval_res["packages_configured"] is True

def test_dbt_project_evaluator_catches_missing_pk_tests():
    project = {
        "marts_models": {"dim_bad": "SELECT 1"},
        "schema_tests_yaml": "version: 2\nmodels:\n  - name: dim_bad\n    columns: []",
        "packages_yaml": "packages: []"
    }
    eval_res = DBTProjectEvaluator.evaluate_project(project)
    assert eval_res["status"] == "FAIL"
    assert any("missing required primary key integrity tests" in v for v in eval_res["violations"])

def test_dbt_project_evaluator_catches_fanout_hazards():
    project = {
        "marts_models": {
            "fact_bad": "SELECT * FROM stg_a CROSS JOIN stg_b"
        },
        "schema_tests_yaml": "",
        "packages_yaml": ""
    }
    eval_res = DBTProjectEvaluator.evaluate_project(project)
    assert eval_res["status"] == "FAIL"
    assert any("contains an explicit CROSS JOIN" in v for v in eval_res["violations"])

def test_dbt_project_evaluator_catches_circular_dependencies():
    project = {
        "marts_models": {
            "model_a": "SELECT * FROM {{ ref('model_b') }}",
            "model_b": "SELECT * FROM {{ ref('model_a') }}"
        },
        "schema_tests_yaml": "",
        "packages_yaml": ""
    }
    eval_res = DBTProjectEvaluator.evaluate_project(project)
    assert eval_res["status"] == "FAIL"
    assert any("Circular dependency cycle detected" in v for v in eval_res["violations"])
