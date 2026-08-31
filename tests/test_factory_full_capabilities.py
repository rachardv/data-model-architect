import os
import pytest
from src.folder_scanner import FolderSchemaScanner
from src.erd_generator import VisualMermaidERDGenerator
from src.contract_compiler import DataContractCompiler
from src.orchestration.captain import CaptainOrchestrator

def test_folder_scanner_on_empty_and_valid_dir(tmp_path):
    # Create sample sql and csv files
    sql_file = tmp_path / "orders.sql"
    sql_file.write_text("CREATE TABLE orders (order_id BIGINT, amount DECIMAL(14,2));")
    
    csv_file = tmp_path / "customers.csv"
    csv_file.write_text("customer_id,customer_name,email\n1,Jane,jane@example.com")
    
    result = FolderSchemaScanner.scan_folder(str(tmp_path))
    assert result["status"] == "SUCCESS"
    assert result["total_files_scanned"] == 2
    table_names = [t["table_name"] for t in result["tables_found"]]
    assert "orders" in table_names
    assert "customers" in table_names

def test_erd_generator_outputs_valid_mermaid():
    tables = [
        {
            "name": "dim_product",
            "type": "DIMENSION",
            "primary_key": "product_sk",
            "columns": [{"name": "product_sk", "type": "BIGINT", "is_inferred": False}]
        },
        {
            "name": "fact_sales",
            "type": "FACT",
            "primary_key": "sale_id",
            "columns": [{"name": "sale_id", "type": "BIGINT", "is_inferred": False}]
        }
    ]
    erd = VisualMermaidERDGenerator.generate_erd("sales", tables)
    assert "erDiagram" in erd
    assert "dim_product" in erd
    assert "fact_sales" in erd

def test_data_contract_compiler():
    rules = [
        {"description": "Price must be positive", "enforcement": "Hard Database CHECK", "definition": "price > 0"}
    ]
    contract = DataContractCompiler.compile_contract("pricing", rules)
    assert "Enterprise Data Contract Specification" in contract
    assert "BR-01" in contract
    assert "price > 0" in contract

def test_captain_autonomous_factory_run():
    captain = CaptainOrchestrator()
    payload = {
        "domain": "retail",
        "branch": "NEW_MODEL",
        "narrative": "A customer purchases products from our retail store.",
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
    output = captain.execute_workflow(payload)
    assert output["status"] == "CERTIFIED_PRODUCTION_READY"
    assert "erDiagram" in output["erd_markdown"]
    assert "Enterprise Data Contract" in output["contract_markdown"]
    assert len(output["generated_sql"]) >= 2
