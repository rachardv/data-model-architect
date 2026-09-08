import os
import pytest
from src.transpiler import SQLDialectTranspiler

def test_transpile_duckdb_to_snowflake():
    duckdb_ddl = """
    CREATE TABLE dim_customer (
        customer_sk VARCHAR(64) PRIMARY KEY,
        customer_name VARCHAR(255) NOT NULL,
        scd_valid_from TIMESTAMPTZ NOT NULL,
        scd_valid_to TIMESTAMPTZ DEFAULT '9999-12-31 UTC'
    );
    """
    snowflake_sql = SQLDialectTranspiler.transpile_sql(duckdb_ddl, read_dialect="duckdb", write_dialect="snowflake")
    assert "CREATE TABLE dim_customer" in snowflake_sql
    assert "customer_sk VARCHAR" in snowflake_sql

def test_transpile_duckdb_to_bigquery():
    duckdb_hash = "SELECT CAST(MD5(customer_id) AS VARCHAR(64)) AS customer_sk FROM raw_customers;"
    bq_sql = SQLDialectTranspiler.transpile_sql(duckdb_hash, read_dialect="duckdb", write_dialect="bigquery")
    # BigQuery requires TO_HEX(MD5(...)) for string hashing
    assert "TO_HEX" in bq_sql or "MD5" in bq_sql
    assert "STRING" in bq_sql

def test_transpile_duckdb_to_postgres():
    duckdb_query = "SELECT customer_id, count(*) AS total_orders FROM orders GROUP BY customer_id;"
    pg_sql = SQLDialectTranspiler.transpile_sql(duckdb_query, read_dialect="duckdb", write_dialect="postgres")
    assert "customer_id" in pg_sql
    assert "GROUP BY" in pg_sql

def test_validate_ast_valid_query():
    sql = """
    SELECT c.customer_name, SUM(o.total_amount) AS revenue
    FROM dim_customers c
    JOIN fact_orders o ON c.customer_sk = o.customer_sk
    WHERE o.order_date >= '2026-01-01'
    GROUP BY c.customer_name;
    """
    ast_info = SQLDialectTranspiler.validate_ast(sql, dialect="duckdb")
    assert ast_info["is_valid"] is True
    assert ast_info["statement_count"] == 1
    assert "SELECT" in ast_info["statement_types"]
    assert "dim_customers" in ast_info["tables_referenced"]
    assert "fact_orders" in ast_info["tables_referenced"]
    assert ast_info["has_joins"] is True
    assert ast_info["error"] is None

def test_validate_ast_syntax_error():
    broken_sql = "SELECT c.customer_name FROM WHERE;"
    ast_info = SQLDialectTranspiler.validate_ast(broken_sql, dialect="duckdb")
    assert ast_info["is_valid"] is False
    assert ast_info["error"] is not None

def test_transpile_pipeline_in_memory():
    pipeline = {
        "bronze": {
            "raw_orders": "CREATE TABLE raw_orders (id INT, amount DECIMAL(14,2));"
        },
        "silver": {
            "stg_orders": "CREATE VIEW stg_orders AS SELECT id, CAST(amount AS DECIMAL(14,2)) AS amount FROM raw_orders;"
        },
        "gold": {
            "fact_orders": "SELECT id, amount FROM stg_orders;"
        }
    }
    
    transpiled = SQLDialectTranspiler.transpile_pipeline(
        pipeline=pipeline,
        target_dialects=["snowflake", "bigquery", "postgres"]
    )
    
    assert "snowflake" in transpiled
    assert "bigquery" in transpiled
    assert "postgres" in transpiled
    assert "raw_orders" in transpiled["snowflake"]["bronze"]
    assert "stg_orders" in transpiled["bigquery"]["silver"]
    assert "fact_orders" in transpiled["postgres"]["gold"]

def test_export_dialects_to_disk(tmp_path):
    pipeline = {
        "bronze": {"raw_t": "CREATE TABLE raw_t (id INT);"},
        "silver": {"stg_t": "CREATE VIEW stg_t AS SELECT id FROM raw_t;"},
        "gold": {"fact_t": "SELECT id FROM stg_t;"}
    }
    
    counts = SQLDialectTranspiler.export_dialects(
        domain="test_domain",
        pipeline=pipeline,
        base_dir=str(tmp_path),
        target_dialects=["snowflake", "postgres"]
    )
    
    assert counts["snowflake"] == 3
    assert counts["postgres"] == 3
    
    sf_gold_file = tmp_path / "test_domain" / "dialects" / "snowflake" / "03_gold" / "fact_t.sql"
    assert os.path.exists(sf_gold_file)
