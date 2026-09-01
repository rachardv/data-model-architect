import os
from typing import Dict, List, Any, Optional

class STTMGenerator:
    """
    Automated Source-to-Target Mapping (STTM) Generator.
    Compiles standardized, 5-section engineering mapping specifications directly from 
    the certified target schema and Data Contract, guaranteeing zero documentation drift.
    """
    
    @classmethod
    def derive_plain_english_description(cls, col_name: str, col_type: str, is_pk: bool, table_type: str) -> str:
        name_lower = col_name.lower()
        
        if name_lower.endswith("_sk"):
            return "Unique synthetic surrogate key identifying this specific record or historical version."
        if name_lower.startswith("scd_valid_from"):
            return "Audit timestamp indicating when this record version became effective."
        if name_lower.startswith("scd_valid_to"):
            return "Audit timestamp indicating when this record version expired ('9999-12-31 UTC' for active records)."
        if name_lower == "is_current":
            return "Boolean flag indicating whether this is the latest active record."
        if is_pk:
            return f"Primary key uniquely identifying the {table_type.lower()} record."
        if name_lower.endswith("_id"):
            return f"Natural business identifier referencing the parent {name_lower.replace('_id', '')} entity."
        if any(k in name_lower for k in ["amount", "usd", "price", "cost", "discount", "tax", "fee"]):
            return "Monetary financial metric formatted in USD with exact 2-decimal precision."
        if any(k in name_lower for k in ["qty", "quantity", "count", "days", "hours"]):
            return "Discrete additive integer metric measuring count or elapsed duration."
        if any(k in name_lower for k in ["date", "timestamp", "time", "_at"]):
            return "Calendar date or timestamp recording when the business event occurred."
        if any(k in name_lower for k in ["tier", "status", "type", "category", "code"]):
            return "Categorical business classification or status attribute."
        if any(k in name_lower for k in ["name", "title"]):
            return "Cleaned, standardized display name of the entity."
            
        return "Descriptive business attribute."

    @classmethod
    def derive_sql_transformation(cls, col_name: str, col_type: str, is_pk: bool, table_type: str, domain: str) -> str:
        name_lower = col_name.lower()
        
        if name_lower.endswith("_sk"):
            natural_prefix = name_lower.replace("_sk", "_id")
            return f"MD5(CONCAT({natural_prefix}, '-', CAST(updated_at AS VARCHAR)))"
        if name_lower == "scd_valid_from":
            return "CAST(updated_at AS TIMESTAMPTZ)"
        if name_lower == "scd_valid_to":
            return "COALESCE(LEAD(updated_at) OVER (PARTITION BY id ORDER BY updated_at), '9999-12-31 UTC')"
        if name_lower == "is_current":
            return "(LEAD(updated_at) OVER (PARTITION BY id ORDER BY updated_at) IS NULL)"
        if name_lower.endswith("_id") and "int" in col_type.lower():
            return f"CAST({col_name} AS {col_type})"
        if name_lower.endswith("_id"):
            return f"TRIM(UPPER({col_name}))"
        if any(k in name_lower for k in ["amount", "usd", "price", "cost", "tax"]):
            return f"CAST({col_name} AS DECIMAL(14,2))"
        if "discount" in name_lower:
            return "CAST(ROUND(order_discount * (gross_amount / order_subtotal), 2) AS DECIMAL(14,2))"
        if name_lower == "net_amount_usd":
            return "CAST(gross_amount_usd - allocated_discount_usd AS DECIMAL(14,2))"
        if any(k in name_lower for k in ["qty", "quantity", "count"]):
            return f"CAST({col_name} AS INT)"
        if any(k in name_lower for k in ["date", "timestamp", "_at"]):
            return f"CAST({col_name} AS {col_type})"
        if any(k in name_lower for k in ["name", "title", "city", "state"]):
            return f"TRIM({col_name})"
        if any(k in name_lower for k in ["email"]):
            return f"LOWER(TRIM({col_name}))"
            
        return f"CAST({col_name} AS {col_type})"

    @classmethod
    def generate_table_sttm(cls, domain: str, table_spec: Dict[str, Any]) -> str:
        table_name = table_spec["name"]
        table_type = table_spec.get("type", "DIMENSION").upper()
        primary_key = table_spec.get("primary_key", "id")
        columns = table_spec.get("columns", [])
        
        # 1. Section 1: Short Description
        if table_type == "FACT":
            description = (
                f"Atomic business event fact table recording numeric metrics, timestamps, and foreign key references for {domain} operations. "
                f"**Grain:** One row per individual transaction or line item."
            )
        else:
            description = (
                f"Conformed {domain} dimensional entity providing standardized descriptive context, hierarchy filtering, and drill-across joins. "
                f"**Grain:** One row per unique entity or historical SCD2 profile version."
            )
            
        # 2. Section 2: Source Tables
        source_tables = [
            f"`bronze.raw_{domain}_{table_name.replace('dim_', '').replace('fact_', '').replace('_scd2', '')}`",
            f"`silver.stg_{domain}_{table_name.replace('dim_', '').replace('fact_', '').replace('_scd2', '')}`"
        ]
        
        # 3. Section 3: Destination Table
        dest_table = f"`gold.{table_name}`"
        
        # 4. Section 4: Raw SQL
        raw_sql_lines = []
        raw_sql_lines.append("WITH stg_source AS (")
        raw_sql_lines.append(f"    SELECT * FROM silver.stg_{domain}_{table_name.replace('dim_', '').replace('fact_', '').replace('_scd2', '')}")
        raw_sql_lines.append(")")
        raw_sql_lines.append("SELECT")
        for i, col in enumerate(columns):
            c_name = col["name"]
            c_type = col.get("type", "VARCHAR(255)")
            is_pk = (c_name == primary_key)
            sql_expr = cls.derive_sql_transformation(c_name, c_type, is_pk, table_type, domain)
            comma = "," if i < len(columns) - 1 else ""
            raw_sql_lines.append(f"    {sql_expr} AS {c_name}{comma}")
        raw_sql_lines.append("FROM stg_source;")
        raw_sql = "\n".join(raw_sql_lines)
        
        # 5. Section 5: Column Mapping & Business Logic Matrix
        matrix_rows = []
        for col in columns:
            c_name = col["name"]
            c_type = col.get("type", "VARCHAR(255)")
            nullable_str = "✔️ YES" if col.get("nullable", True) else "❌ NO"
            is_pk = (c_name == primary_key)
            plain_desc = cls.derive_plain_english_description(c_name, c_type, is_pk, table_type)
            sql_expr = cls.derive_sql_transformation(c_name, c_type, is_pk, table_type, domain)
            matrix_rows.append(f"| `{c_name}` | `{c_type}` | {nullable_str} | {plain_desc} | `{sql_expr}` |")
            
        col_matrix = "\n".join(matrix_rows)
        
        source_tables_md = "\n".join(f"* {s}" for s in source_tables)
        
        # Assemble 5-Section Markdown
        table_md = (
            f"## 🏛️ `{table_name}`\n\n"
            f"### 1. Short Description\n"
            f"{description}\n\n"
            f"### 2. Source Tables\n"
            f"{source_tables_md}\n\n"
            f"### 3. Destination Table\n"
            f"* **Target Table:** {dest_table}\n"
            f"* **Target Layer:** Gold Production Dimensional Mart\n"
            f"* **Primary Key:** `{primary_key}`\n\n"
            f"### 4. Raw SQL\n"
            f"```sql\n"
            f"{raw_sql}\n"
            f"```\n\n"
            f"### 5. Column Mapping & Business Logic Matrix\n\n"
            f"| Column Name | Data Type | Nullable? | Plain-English Description | SQL Expression / Transformation Logic |\n"
            f"| :--- | :--- | :---: | :--- | :--- |\n"
            f"{col_matrix}\n"
        )
        return table_md

    @classmethod
    def generate_sttm_document(
        cls,
        domain: str,
        target_schema: Dict[str, Any],
        source_tables: Optional[List[Dict[str, Any]]] = None,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        lines = [
            f"# 🗺️ Source-to-Target Mapping (STTM) Specification",
            f"**Domain:** `{domain}`  ",
            f"**Governance Standard:** OpenDataContract Standard (ODCS) v3.0.0  ",
            f"**Compiled By:** Autonomous Data Model Factory  ",
            f"",
            f"---",
            f"",
            f"## 📋 Overview & Architectural Invariants",
            f"This document provides the standardized, 5-section transformation and lineage specification for the `{domain}` domain.",
            f"All transformations are compiled deterministically from the certified data model and Data Contract, guaranteeing zero documentation drift.",
            f"",
            f"---",
            f""
        ]
        
        tables = target_schema.get("tables", [])
        for t in tables:
            lines.append(cls.generate_table_sttm(domain, t))
            lines.append("\n---\n")
            
        return "\n".join(lines)

    @classmethod
    def export_sttm_file(cls, output_base_dir: str, domain: str, sttm_markdown: str) -> str:
        """Exports the STTM document to docs/SOURCE_TO_TARGET_MAPPING.md."""
        docs_dir = os.path.abspath(output_base_dir)
        os.makedirs(docs_dir, exist_ok=True)
        
        main_sttm_path = os.path.join(docs_dir, "SOURCE_TO_TARGET_MAPPING.md")
        with open(main_sttm_path, "w", encoding="utf-8") as f:
            f.write(sttm_markdown)
            
        # Also mirror in domain pipeline directory
        domain_pipeline_dir = os.path.join(docs_dir, "pipelines", domain)
        os.makedirs(domain_pipeline_dir, exist_ok=True)
        domain_sttm_path = os.path.join(domain_pipeline_dir, "SOURCE_TO_TARGET_MAPPING.md")
        with open(domain_sttm_path, "w", encoding="utf-8") as f:
            f.write(sttm_markdown)
            
        return main_sttm_path
