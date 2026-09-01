import sys
import os
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.sttm_generator import STTMGenerator
from src.orchestration.captain import CaptainOrchestrator

def test_sttm_generator_table_sections():
    table_spec = {
        "name": "dim_customer_scd2",
        "type": "DIMENSION",
        "primary_key": "customer_sk",
        "columns": [
            {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False},
            {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False},
            {"name": "customer_name", "type": "VARCHAR(255)", "nullable": False},
            {"name": "loyalty_tier", "type": "VARCHAR(50)", "nullable": False},
            {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False},
            {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False}
        ]
    }
    
    sttm_md = STTMGenerator.generate_table_sttm("ecommerce", table_spec)
    
    # Verify all 5 mandatory sections exist
    assert "### 1. Short Description" in sttm_md
    assert "### 2. Source Tables" in sttm_md
    assert "### 3. Destination Table" in sttm_md
    assert "### 4. Raw SQL" in sttm_md
    assert "### 5. Column Mapping & Business Logic Matrix" in sttm_md
    
    # Verify Column Mapping Matrix Headers
    assert "| Column Name | Data Type | Nullable? | Plain-English Description | SQL Expression / Transformation Logic |" in sttm_md
    assert "| `customer_sk` | `VARCHAR(64)` | ❌ NO |" in sttm_md
    assert "| `scd_valid_to` | `TIMESTAMPTZ` | ❌ NO |" in sttm_md

def test_sttm_generator_full_document():
    target_schema = {
        "tables": [
            {
                "name": "dim_customer_scd2",
                "type": "DIMENSION",
                "primary_key": "customer_sk",
                "columns": [
                    {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False},
                    {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False}
                ]
            },
            {
                "name": "fact_orders",
                "type": "FACT",
                "primary_key": "order_id",
                "columns": [
                    {"name": "order_id", "type": "BIGINT", "nullable": False},
                    {"name": "total_amount_usd", "type": "DECIMAL(14,2)", "nullable": False}
                ]
            }
        ]
    }
    
    doc = STTMGenerator.generate_sttm_document("ecommerce", target_schema)
    assert "# 🗺️ Source-to-Target Mapping (STTM) Specification" in doc
    assert "## 🏛️ `dim_customer_scd2`" in doc
    assert "## 🏛️ `fact_orders`" in doc

def test_captain_orchestrator_exports_sttm():
    captain = CaptainOrchestrator(output_dir="docs")
    payload = {
        "domain": "ecommerce",
        "narrative": "A customer browses products online and places an order. The order is fulfilled from a local retail store or shipped from a regional warehouse.",
        "business_answers": [
            "We want to build executive dashboards, BI reports, and analyze sales trends over time.",
            "Past historical reports should preserve the original customer address at the time of purchase.",
            "No, we only need to record each individual transaction as a single standalone event."
        ]
    }
    result = captain.execute_workflow(payload)
    
    assert result["status"] == "CERTIFIED_PRODUCTION_READY"
    assert "sttm_markdown" in result
    assert "sttm_file_path" in result
    assert os.path.exists(result["sttm_file_path"])
    
    with open(result["sttm_file_path"], "r", encoding="utf-8") as f:
        content = f.read()
        assert "### 1. Short Description" in content
        assert "### 5. Column Mapping & Business Logic Matrix" in content
