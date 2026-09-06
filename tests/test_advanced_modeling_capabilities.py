import pytest
import os
import tempfile
import duckdb
from src.folder_scanner import FolderSchemaScanner
from src.ddl_generator import ANSISQLGenerator
from src.decision_engine import DataModelDecisionEngine
from src.orchestration.reviewer_council import ReviewerCouncil
from src.sttm_generator import STTMGenerator

def test_multi_table_sql_scanner(tmp_path):
    # Create a single SQL file with multiple tables and comments
    sql_content = """-- =========================================================
-- Multi-Table Production DDL Script with Comments
-- =========================================================

-- Table 1: Customers
CREATE TABLE dim_customer (
    customer_id BIGINT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    -- Address details
    email VARCHAR(128)
);

/* Table 2: Products
   Stores product catalog
*/
CREATE TABLE dim_product (
    product_id BIGINT,
    sku VARCHAR(64),
    price DECIMAL(10,2),
    CONSTRAINT pk_dim_product PRIMARY KEY (product_id)
);

-- Table 3: Orders
CREATE TABLE fact_orders (
    order_id BIGINT,
    customer_id BIGINT,
    total_usd DECIMAL(14,2),
    CONSTRAINT pk_fact_orders PRIMARY KEY (order_id)
);
"""
    sql_file = tmp_path / "production_schema.sql"
    sql_file.write_text(sql_content, encoding="utf-8")
    
    res = FolderSchemaScanner.scan_folder(str(tmp_path))
    tables = res["tables_found"]
    
    # Must parse into 3 distinct tables, NOT 1
    assert len(tables) == 3
    table_names = [t["table_name"] for t in tables]
    assert "dim_customer" in table_names
    assert "dim_product" in table_names
    assert "fact_orders" in table_names
    
    # Check dim_customer columns (must not have comment artifacts)
    customer_table = next(t for t in tables if t["table_name"] == "dim_customer")
    c_cols = [c["name"] for c in customer_table["columns"]]
    assert "customer_id" in c_cols
    assert "customer_name" in c_cols
    assert "email" in c_cols
    assert "address" not in c_cols  # From comment "-- Address details"

def test_multi_currency_fact_triad():
    triad_cols = ANSISQLGenerator.generate_multi_currency_columns(measure_name="order_amount", target_currency="usd")
    col_names = [c["name"] for c in triad_cols]
    
    assert "order_amount_local" in col_names
    assert "currency_code" in col_names
    assert "exchange_rate_to_usd" in col_names
    assert "order_amount_usd" in col_names
    
    # Verify ReviewerCouncil catches missing FX triad when is_multi_currency is True
    bad_spec = {
        "is_multi_currency": True,
        "tables": [{
            "name": "fact_sales",
            "type": "FACT",
            "columns": [{"name": "total_amount", "type": "DECIMAL(14,2)"}]
        }]
    }
    audit_bad = ReviewerCouncil.audit_model(bad_spec)
    assert not audit_bad["passed"]
    assert any("Multi-Currency FX" in f["title"] for f in audit_bad["findings"])
    
    # Verify ReviewerCouncil passes when triad is present
    good_spec = {
        "is_multi_currency": True,
        "tables": [{
            "name": "fact_sales",
            "type": "FACT",
            "columns": triad_cols
        }]
    }
    audit_good = ReviewerCouncil.audit_model(good_spec)
    assert not any("Multi-Currency FX" in f["title"] for f in audit_good["findings"])

def test_jsonb_polymorphic_column_support():
    columns = [
        {"name": "product_id", "type": "BIGINT", "nullable": False},
        {"name": "product_name", "type": "VARCHAR(255)", "nullable": False},
        {"name": "custom_attributes", "type": "JSONB", "nullable": True}
    ]
    sql = ANSISQLGenerator.generate_table_sql("dim_product_catalog", columns, "product_id")
    assert "custom_attributes" in sql
    assert "JSONB" in sql

def test_recursive_closure_table_generation():
    # 1. Decision engine classification
    arch = DataModelDecisionEngine.classify_architecture(
        is_live_app=False,
        is_high_frequency_stream=False,
        needs_history=True,
        has_retroactive_backdating=False,
        has_multi_stage_milestones=False,
        is_periodic_state_rollup=False,
        has_high_churn_ml_scores=False,
        has_recursive_hierarchy=True
    )
    assert arch["pattern"] == "RECURSIVE_HIERARCHY_CLOSURE"
    assert arch["storage"] == "Kimball Closure Bridge Table"
    
    # 2. DDL generator
    closure_sql = ANSISQLGenerator.generate_closure_table_sql("part", "BIGINT")
    assert "CREATE TABLE bridge_part_closure" in closure_sql
    assert "ancestor_part_id" in closure_sql
    assert "descendant_part_id" in closure_sql
    assert "depth_level" in closure_sql
    assert "is_leaf" in closure_sql

def test_drill_across_cte_generation():
    drill_sql = STTMGenerator.generate_drill_across_cte(
        fact1_name="fact_order_actuals",
        fact1_metric="sales_amount_usd",
        fact2_name="fact_monthly_budget",
        fact2_metric="budget_amount_usd",
        conformed_dim_keys=["department_sk", "date_sk"]
    )
    assert "WITH fact_order_actuals_agg AS" in drill_sql
    assert "fact_monthly_budget_agg AS" in drill_sql
    assert "FULL OUTER JOIN fact_monthly_budget_agg" in drill_sql
    assert "variance_metric" in drill_sql

def test_duckdb_execution_of_closure_table():
    closure_sql = ANSISQLGenerator.generate_closure_table_sql("employee", "BIGINT")
    con = duckdb.connect(database=":memory:")
    # DuckDB should execute this DDL with zero errors
    con.execute(closure_sql)
    
    # Insert a sample 3-tier hierarchy: CEO (1) -> VP (2) -> Dev (3)
    con.execute("""
    INSERT INTO bridge_employee_closure VALUES 
        (1, 1, 0, false),
        (1, 2, 1, false),
        (1, 3, 2, true),
        (2, 2, 0, false),
        (2, 3, 1, true),
        (3, 3, 0, true);
    """)
    
    res = con.execute("SELECT COUNT(*) FROM bridge_employee_closure WHERE ancestor_employee_id = 1").fetchone()[0]
    assert res == 3
