import os
from typing import Dict, List, Any, Optional

class STTMGenerator:
    """
    Automated Source-to-Target Mapping (STTM) Generator.
    Compiles standardized, 5-section engineering mapping specifications directly from 
    the certified target schema and Data Contract, guaranteeing zero documentation drift.
    Supports Kimball Multi-Fact Drill-Across Bus queries, Multi-Currency Triads, and JSONB.
    """
    
    @classmethod
    def derive_plain_english_description(cls, col_name: str, col_type: str, is_pk: bool, table_type: str) -> str:
        name_lower = col_name.lower()
        type_upper = col_type.upper()
        
        if type_upper in ["JSONB", "VARIANT", "RECORD"]:
            return "Semi-structured JSON document storing dynamic polymorphic attributes without schema migration."
        if name_lower.endswith("_local"):
            return "Monetary financial metric recorded in original local transaction currency."
        if name_lower == "currency_code":
            return "ISO-4217 standard 3-letter currency code (e.g. USD, EUR, GBP, JPY)."
        if name_lower.startswith("exchange_rate_to_"):
            return "Daily spot foreign exchange conversion rate to normalized target currency."
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
            return "Monetary financial metric formatted with exact 2-decimal precision."
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
        type_upper = col_type.upper()
        
        if type_upper in ["JSONB", "VARIANT", "RECORD"]:
            return f"CAST({col_name} AS JSONB)"
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
        if name_lower == "currency_code":
            return f"TRIM(UPPER(COALESCE({col_name}, 'USD')))"
        if name_lower.startswith("exchange_rate_to_"):
            return f"COALESCE(CAST({col_name} AS DECIMAL(12,6)), 1.000000)"
        if any(k in name_lower for k in ["amount", "usd", "price", "cost", "tax", "_local"]):
            return f"CAST({col_name} AS DECIMAL(14,2))"
        if "discount" in name_lower:
            return "CAST(ROUND(order_discount * (gross_amount / order_subtotal), 2) AS DECIMAL(14,2))"
        if any(k in name_lower for k in ["qty", "quantity", "count", "days"]):
            return f"COALESCE(CAST({col_name} AS INT), 0)"
        if any(k in name_lower for k in ["date", "timestamp", "_at"]):
            return f"CAST({col_name} AS TIMESTAMPTZ)"
        if any(k in name_lower for k in ["tier", "status", "type"]):
            return f"TRIM(UPPER({col_name}))"
            
        return f"TRIM({col_name})"

    @classmethod
    def generate_point_in_time_fact_join(
        cls,
        fact_alias: str,
        dim_table_name: str,
        dim_alias: str,
        join_key: str,
        timestamp_col: str = "event_timestamp"
    ) -> str:
        """
        Generates standard Kimball Point-in-Time Range Join for SCD2 historical resolution.
        Accurately resolves surrogate keys for late-arriving facts.
        """
        return f"""LEFT JOIN gold.{dim_table_name} {dim_alias}
    ON {fact_alias}.{join_key} = {dim_alias}.{join_key}
   AND {fact_alias}.{timestamp_col} >= {dim_alias}.scd_valid_from
   AND {fact_alias}.{timestamp_col} < {dim_alias}.scd_valid_to"""

    @classmethod
    def generate_drill_across_cte(
        cls,
        fact1_name: str,
        fact1_metric: str,
        fact2_name: str,
        fact2_metric: str,
        conformed_dim_keys: List[str]
    ) -> str:
        """
        Generates standard Kimball Drill-Across SQL CTE for multi-fact comparison (e.g. Budget vs Actuals).
        Pre-aggregates each fact to the common conformed dimension grain before joining,
        completely preventing the Chasm Trap / Cartesian row multiplication.
        """
        keys_str = ", ".join(conformed_dim_keys)
        f1_select_keys = ", ".join([f"COALESCE(f1.{k}, f2.{k}) AS {k}" for k in conformed_dim_keys])
        join_conditions = " AND ".join([f"f1.{k} = f2.{k}" for k in conformed_dim_keys])
        
        return f"""-- ====================================================================
-- KIMBALL DRILL-ACROSS BUS QUERY: {fact1_name.upper()} VS {fact2_name.upper()}
-- Prevents Chasm Trap by pre-aggregating each fact to conformed grain
-- ====================================================================
WITH {fact1_name}_agg AS (
    SELECT 
        {keys_str},
        SUM({fact1_metric}) AS total_{fact1_metric}
    FROM gold.{fact1_name}
    GROUP BY {keys_str}
),
{fact2_name}_agg AS (
    SELECT 
        {keys_str},
        SUM({fact2_metric}) AS total_{fact2_metric}
    FROM gold.{fact2_name}
    GROUP BY {keys_str}
)
SELECT 
    {f1_select_keys},
    COALESCE(f1.total_{fact1_metric}, 0.00) AS total_{fact1_metric},
    COALESCE(f2.total_{fact2_metric}, 0.00) AS total_{fact2_metric},
    (COALESCE(f1.total_{fact1_metric}, 0.00) - COALESCE(f2.total_{fact2_metric}, 0.00)) AS variance_metric
FROM {fact1_name}_agg f1
FULL OUTER JOIN {fact2_name}_agg f2
    ON {join_conditions};"""

    @classmethod
    def generate_table_sttm(
        cls, 
        domain: str, 
        target_table: Dict[str, Any], 
        source_tables: Optional[List[Dict[str, Any]]] = None,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        table_name = target_table["name"]
        table_type = target_table.get("type", "TABLE")
        primary_key = target_table.get("primary_key", "id")
        columns = target_table.get("columns", [])
        
        # 1. Short Description
        desc = target_table.get("description", "")
        if not desc:
            if table_type == "FACT":
                desc = f"Core transactional fact table recording {domain} business activity at atomic grain."
            elif table_type == "DIMENSION":
                desc = f"Conformed reference dimension providing business context, filtering, and grouping attributes for {domain} entities."
            elif table_type == "BRIDGE":
                desc = f"Kimball multi-valued bridge table decoupling parent-child or many-to-many associations for {domain} entities."
            else:
                desc = f"Standard relational entity table storing {domain} records."
                
        # 2. Source Tables
        source_names = [s.get("table_name", s.get("source_file", "raw_source")) for s in (source_tables or [])]
        if not source_names:
            source_names = [f"bronze.raw_{domain}_events", f"silver.stg_{domain}_clean"]
            
        sources_md = "\n".join([f"- `{src}`" for src in source_names])
        
        # 3. Destination Table
        dest_md = f"- **Table Name**: `{table_name}`\n- **Type**: `{table_type}`\n- **Primary Key**: `{primary_key}`"
        
        # 4. Raw SQL (CTE)
        col_selects = []
        for col in columns:
            col_name = col["name"]
            col_type = col.get("type", "VARCHAR(255)")
            is_pk = (col_name == primary_key)
            trans = cls.derive_sql_transformation(col_name, col_type, is_pk, table_type, domain)
            col_selects.append(f"    {trans:<70} AS {col_name}")
            
        select_clause = ",\n".join(col_selects)
        from_table = source_names[0] if source_names else f"bronze.raw_{domain}_source"
        
        raw_sql = f"""WITH source_clean AS (
    SELECT *
    FROM {from_table}
    WHERE is_valid = TRUE
)
SELECT
{select_clause}
FROM source_clean;"""

        # 5. Column Mapping Matrix
        matrix_rows = []
        for col in columns:
            col_name = col["name"]
            col_type = col.get("type", "VARCHAR(255)")
            nullable = "YES" if col.get("nullable", True) else "❌ NO"
            is_pk = (col_name == primary_key)
            plain_desc = cls.derive_plain_english_description(col_name, col_type, is_pk, table_type)
            sql_trans = cls.derive_sql_transformation(col_name, col_type, is_pk, table_type, domain)
            
            # Escape pipes for markdown table
            plain_desc = plain_desc.replace("|", "/")
            sql_trans = sql_trans.replace("|", "/")
            
            matrix_rows.append(f"| `{col_name}` | `{col_type}` | {nullable} | {plain_desc} | `{sql_trans}` |")
            
        matrix_table = (
            "| Column Name | Data Type | Nullable? | Plain-English Description | SQL Expression / Transformation Logic |\n"
            "| :--- | :--- | :---: | :--- | :--- |\n" +
            "\n".join(matrix_rows)
        )
        
        return f"""## 🏛️ `{table_name}`

### 1. Short Description
{desc}

### 2. Source Tables
{sources_md}

### 3. Destination Table
{dest_md}

### 4. Raw SQL (Production Transformation CTE)
```sql
{raw_sql}
```

### 5. Column Mapping & Business Logic Matrix
{matrix_table}
"""

    @classmethod
    def generate_sttm_document(
        cls, 
        domain: str, 
        target_schema: Dict[str, Any], 
        source_tables: Optional[List[Dict[str, Any]]] = None,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        lines = [
            f"# 🗺️ Source-to-Target Mapping (STTM) Specification: `{domain.upper()}`",
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
            lines.append(cls.generate_table_sttm(domain, t, source_tables, rules))
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
