import pytest
from src.medallion_generator import MedallionPipelineGenerator
from src.sql_runner import DuckDBPipelineRunner

def test_duckdb_end_to_end_pipeline_execution():
    domain = "retail"
    target_schema = {
        "tables": [
            {
                "name": f"dim_{domain}_customer_core",
                "type": "DIMENSION",
                "is_conformed": True,
                "columns": [
                    {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                    {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                    {"name": "customer_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                    {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                    {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 23:59:59 UTC'"}
                ],
                "primary_key": "customer_sk"
            },
            {
                "name": f"fact_{domain}_orders",
                "type": "FACT",
                "columns": [
                    {"name": "order_id", "type": "BIGINT", "nullable": False, "is_inferred": False},
                    {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
                    {"name": "estimated_delivery_days", "type": "INT", "nullable": True, "is_inferred": True}
                ],
                "primary_key": "order_id"
            }
        ],
        "temporal_strategy": "SCD2"
    }
    rules = [
        {"description": "Total amount must be non-negative", "enforcement": "Hard Database CHECK", "definition": "total_amount_usd >= 0.00"},
        {"description": "Estimated delivery days must be positive", "enforcement": "Hard Database CHECK", "definition": "estimated_delivery_days > 0"}
    ]

    pipeline = MedallionPipelineGenerator.generate_full_pipeline(
        domain=domain,
        source_tables=None,
        target_schema=target_schema,
        rules=rules
    )

    result = DuckDBPipelineRunner.execute_and_verify(
        domain=domain,
        target_schema=target_schema,
        pipeline=pipeline
    )

    assert result["status"] == "EXECUTION_VERIFIED"
    assert "DuckDB" in result["engine"]
    assert result["bronze"][f"raw_{domain}_customers"]["rows_inserted"] == 3
    assert result["bronze"][f"raw_{domain}_orders"]["rows_inserted"] == 3
    assert result["silver"][f"stg_{domain}_customers"]["view_rows"] == 2
    assert result["silver"][f"stg_{domain}_orders"]["view_rows"] == 2
    assert result["quarantine_records_isolated"] == 1
    assert result["gold"][f"dim_{domain}_customer_core"]["final_rows"] == 2
    assert result["gold"][f"fact_{domain}_orders"]["final_rows"] == 2
