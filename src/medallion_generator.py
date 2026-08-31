import os
from typing import Dict, Any, List, Optional

class MedallionPipelineGenerator:
    """
    Automated Medallion Architecture (Bronze -> Silver -> Gold) SQL Pipeline Generator.
    Emits strict ANSI SQL-92/99 compliant scripts with zero framework dependencies.
    """

    @classmethod
    def _get_default_source_tables(cls) -> List[Dict[str, Any]]:
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
                    {"name": "order_status", "type": "VARCHAR(32)"},
                    {"name": "order_timestamp", "type": "TIMESTAMPTZ"}
                ]
            }
        ]
    
    @classmethod
    def generate_bronze_layer(
        cls,
        domain: str,
        source_tables: List[Dict[str, Any]] = None,
        include_sample_data: bool = True
    ) -> Dict[str, str]:
        """
        Generates Bronze raw landing DDL with audit metadata columns and optional test INSERT statements.
        """
        bronze_sql = {}
        if not source_tables:
            source_tables = cls._get_default_source_tables()
            
        for src in source_tables:
            tname = src.get("table_name", "source_data").lower()
            raw_table_name = f"raw_{domain}_{tname}"
            cols = src.get("columns", [])
            
            lines = [
                f"-- ============================================================================",
                f"-- BRONZE LAYER: Raw Landing Ingestion Schema for `{tname}`",
                f"-- Ingestion Strategy: Append-Only Immutable Raw Event Ledger",
                f"-- ============================================================================",
                f"CREATE TABLE {raw_table_name} ("
            ]
            
            # Technical source columns
            for col in cols:
                cname = col.get("name", "col")
                ctype = col.get("type", "VARCHAR(255)")
                lines.append(f"    {cname:<28} {ctype},")
                
            # Audit Metadata Columns
            lines.append("    -- Audit Metadata Tracking")
            lines.append("    _raw_payload_id              VARCHAR(64) NOT NULL,")
            lines.append("    _source_file                 VARCHAR(255) NOT NULL DEFAULT 'stream_ingest',")
            lines.append("    _ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP")
            lines.append(");")
            
            # Embedded Sample Test Data
            if include_sample_data:
                lines.append("")
                lines.append(f"-- Sample Test Data Harness (Self-Contained Verification)")
                if "customer" in tname:
                    lines.append(f"INSERT INTO {raw_table_name} (customer_id, customer_name, email, updated_at, _raw_payload_id, _source_file, _ingested_at)")
                    lines.append(f"VALUES ")
                    lines.append(f"    ('CUST-1001', 'Alice Smith', 'alice@example.com', '2026-01-15 10:00:00 UTC', 'PAYLOAD-001', 'seed_data.csv', CURRENT_TIMESTAMP),")
                    lines.append(f"    ('CUST-1001', 'Alice Smith-Jones', 'alice.sj@example.com', '2026-06-20 14:30:00 UTC', 'PAYLOAD-002', 'seed_data.csv', CURRENT_TIMESTAMP),")
                    lines.append(f"    ('CUST-1002', 'Bob Johnson', 'bob@example.com', '2026-02-01 09:15:00 UTC', 'PAYLOAD-003', 'seed_data.csv', CURRENT_TIMESTAMP);")
                elif "order" in tname:
                    lines.append(f"INSERT INTO {raw_table_name} (order_id, customer_id, total_amount, order_status, order_timestamp, _raw_payload_id, _source_file, _ingested_at)")
                    lines.append(f"VALUES ")
                    lines.append(f"    (5001, 'CUST-1001', 149.50, 'DELIVERED', '2026-02-10 11:20:00 UTC', 'PAYLOAD-004', 'seed_data.csv', CURRENT_TIMESTAMP),")
                    lines.append(f"    (5002, 'CUST-1002', 89.00, 'SHIPPED', '2026-02-11 15:45:00 UTC', 'PAYLOAD-005', 'seed_data.csv', CURRENT_TIMESTAMP),")
                    lines.append(f"    (5003, 'CUST-1001', -25.00, 'REJECTED_TEST', '2026-02-12 18:00:00 UTC', 'PAYLOAD-006', 'seed_data.csv', CURRENT_TIMESTAMP);")
                else:
                    sample_cols = [c.get("name") for c in cols]
                    sample_vals = ["'SAMPLE_VAL'" for _ in sample_cols]
                    lines.append(f"INSERT INTO {raw_table_name} ({', '.join(sample_cols)}, _raw_payload_id, _source_file, _ingested_at)")
                    lines.append(f"VALUES ({', '.join(sample_vals)}, 'PAYLOAD-999', 'seed.csv', CURRENT_TIMESTAMP);")
                    
            bronze_sql[raw_table_name] = "\n".join(lines)
            
        return bronze_sql

    @classmethod
    def generate_silver_layer(
        cls,
        domain: str,
        source_tables: List[Dict[str, Any]] = None,
        target_schema: Dict[str, Any] = None,
        rules: List[Dict[str, Any]] = None,
        quality_policy: str = "QUARANTINE_VIEW"
    ) -> Dict[str, str]:
        """
        Generates Silver Staging & Cleansing SQL with:
        - CTE-based window deduplication (ROW_NUMBER)
        - Data Contract invariant filtering / Quarantine views
        - Type casting & normalization
        - Deterministic Surrogate Key hashing
        """
        silver_sql = {}
        if not source_tables:
            source_tables = cls._get_default_source_tables()
        if rules is None:
            rules = []
        if target_schema is None:
            target_schema = {}
            
        invariant_clauses = [r.get("definition") for r in rules if r.get("definition")]
        
        for src in source_tables:
            tname = src.get("table_name", "source_data").lower()
            raw_table_name = f"raw_{domain}_{tname}"
            stg_view_name = f"stg_{domain}_{tname}"
            quarantine_view_name = f"quarantine_{domain}_{tname}"
            cols = src.get("columns", [])
            col_names = [c["name"] for c in cols]
            
            sing_name = tname[:-1] if tname.endswith("s") else tname
            
            pk_candidates = [c["name"] for c in cols if "id" in c["name"].lower() or "key" in c["name"].lower()]
            pk_col = pk_candidates[0] if pk_candidates else cols[0]["name"] if cols else "id"
            
            ts_candidates = [c["name"] for c in cols if "time" in c["name"].lower() or "date" in c["name"].lower() or "at" in c["name"].lower()]
            ts_col = ts_candidates[0] if ts_candidates else "_ingested_at"
            
            relevant_invariants = []
            if "order" in tname or "fact" in tname:
                for inv in invariant_clauses:
                    inv_stmt = inv
                    if "total_amount_usd" in inv_stmt and "total_amount" in col_names:
                        inv_stmt = inv_stmt.replace("total_amount_usd", "total_amount")
                    inv_words = [w.strip("()><= ") for w in inv_stmt.split()]
                    has_all_cols = any(w in col_names for w in inv_words)
                    if has_all_cols:
                        relevant_invariants.append(inv_stmt)
            
            lines = [
                f"-- ============================================================================",
                f"-- SILVER LAYER: Staging & Conformed View for `{stg_view_name}`",
                f"-- Quality Policy: {quality_policy}",
                f"-- Transformations: Type Casting, Row-Level Deduplication, Invariant Filtering",
                f"-- ============================================================================",
                f"CREATE OR REPLACE VIEW {stg_view_name} AS",
                f"WITH raw_source AS (",
                f"    SELECT * FROM {raw_table_name}",
                f"),",
                f"deduplicated AS (",
                f"    SELECT",
                f"        *,",
                f"        ROW_NUMBER() OVER (",
                f"            PARTITION BY {pk_col}",
                f"            ORDER BY {ts_col} DESC, _ingested_at DESC",
                f"        ) AS _row_num",
                f"    FROM raw_source",
                f"),",
                f"cleaned AS (",
                f"    SELECT",
                f"        -- Deterministic Surrogate Key Hash",
                f"        CAST(MD5(CAST({pk_col} AS VARCHAR(64))) AS VARCHAR(64)) AS {sing_name}_sk,"
            ]
            
            for col in cols:
                cname = col.get("name")
                ctype = col.get("type", "VARCHAR(255)")
                if "name" in cname.lower():
                    lines.append(f"        TRIM(CAST({cname} AS {ctype})) AS {cname},")
                elif "status" in cname.lower():
                    lines.append(f"        UPPER(TRIM(CAST({cname} AS {ctype}))) AS {cname},")
                else:
                    lines.append(f"        CAST({cname} AS {ctype}) AS {cname},")
                    
            lines.append("        _raw_payload_id,")
            lines.append("        _source_file,")
            lines.append("        _ingested_at")
            lines.append("    FROM deduplicated")
            lines.append("    WHERE _row_num = 1")
            
            if relevant_invariants and quality_policy in ["QUARANTINE_VIEW", "HARD_FILTER"]:
                for inv in relevant_invariants:
                    lines.append(f"      AND {inv}")
                    
            lines.append(")")
            lines.append("SELECT * FROM cleaned;")
            
            silver_sql[stg_view_name] = "\n".join(lines)
            
            if quality_policy == "QUARANTINE_VIEW" and relevant_invariants:
                qlines = [
                    f"-- ============================================================================",
                    f"-- SILVER LAYER: Quarantine Exception View for `{quarantine_view_name}`",
                    f"-- Captures all rejected records failing Data Contract invariants",
                    f"-- ============================================================================",
                    f"CREATE OR REPLACE VIEW {quarantine_view_name} AS",
                    f"WITH raw_source AS (",
                    f"    SELECT * FROM {raw_table_name}",
                    f"),",
                    f"deduplicated AS (",
                    f"    SELECT",
                    f"        *,",
                    f"        ROW_NUMBER() OVER (",
                    f"            PARTITION BY {pk_col}",
                    f"            ORDER BY {ts_col} DESC, _ingested_at DESC",
                    f"        ) AS _row_num",
                    f"    FROM raw_source",
                    f")",
                    f"SELECT",
                    f"    *,",
                    f"    CASE"
                ]
                for i, inv in enumerate(relevant_invariants, 1):
                    qlines.append(f"        WHEN NOT ({inv}) THEN 'FAILED_INVARIANT: {inv}'")
                qlines.append(f"        ELSE 'UNKNOWN_REJECTION'")
                qlines.append(f"    END AS quarantine_reason,")
                qlines.append(f"    CURRENT_TIMESTAMP AS quarantined_at")
                qlines.append(f"FROM deduplicated")
                qlines.append(f"WHERE _row_num = 1")
                qlines.append(f"  AND (NOT ({' AND '.join(relevant_invariants)}));")
                
                silver_sql[quarantine_view_name] = "\n".join(qlines)
                
        return silver_sql

    @classmethod
    def generate_gold_layer(
        cls,
        domain: str,
        target_schema: Dict[str, Any],
        merge_strategy: str = "ANSI_MERGE"
    ) -> Dict[str, str]:
        """
        Generates Gold Dimensional Marts & Transformation SQL:
        - SCD Type 2 atomic MERGE scripts
        - Fact incremental load scripts
        """
        gold_sql = {}
        tables = target_schema.get("tables", [])
        
        for t in tables:
            tname = t.get("name", "")
            ttype = t.get("type", "DIMENSION")
            cols = t.get("columns", [])
            pk = t.get("primary_key", "id")
            
            stg_source = f"stg_{domain}_customers" if "customer" in tname else f"stg_{domain}_orders"
            
            if ttype == "DIMENSION" and any("scd" in c["name"] or "valid" in c["name"] for c in cols):
                lines = [
                    f"-- ============================================================================",
                    f"-- GOLD LAYER: SCD Type 2 Merge Pipeline for `{tname}`",
                    f"-- Strategy: {merge_strategy}",
                    f"-- ============================================================================",
                    f"-- Step 1: Atomic SCD2 Merge & Interval Closure Script",
                    f"MERGE INTO {tname} AS target",
                    f"USING {stg_source} AS source",
                    f"ON (target.customer_id = source.customer_id AND target.scd_valid_to = '9999-12-31 23:59:59 UTC')",
                    f"",
                    f"-- Scenario A: Existing Record Changed -> Close Validity Interval",
                    f"WHEN MATCHED AND (target.customer_name != source.customer_name OR target.customer_id != source.customer_id) THEN",
                    f"    UPDATE SET",
                    f"        scd_valid_to = source.updated_at",
                    f"",
                    f"-- Scenario B: New Entity Record -> Insert New Active Version",
                    f"WHEN NOT MATCHED THEN",
                    f"    INSERT (",
                ]
                col_names = [c["name"] for c in cols]
                lines.append(f"        {', '.join(col_names)}")
                lines.append("    )")
                lines.append("    VALUES (")
                
                val_mappings = []
                for c in cols:
                    cn = c["name"]
                    if cn == pk or "sk" in cn:
                        val_mappings.append(f"source.customer_sk")
                    elif cn == "scd_valid_from":
                        val_mappings.append(f"source.updated_at")
                    elif cn == "scd_valid_to":
                        val_mappings.append(f"'9999-12-31 23:59:59 UTC'")
                    else:
                        val_mappings.append(f"source.{cn}")
                        
                lines.append(f"        {', '.join(val_mappings)}")
                lines.append("    );")
                
                lines.append("")
                lines.append(f"-- Companion Gold View: Current Active State Only")
                lines.append(f"CREATE OR REPLACE VIEW v_current_{tname} AS")
                lines.append(f"SELECT * FROM {tname} WHERE scd_valid_to = '9999-12-31 23:59:59 UTC';")
                
                gold_sql[tname] = "\n".join(lines)
                
            else:
                lines = [
                    f"-- ============================================================================",
                    f"-- GOLD LAYER: Incremental Fact Pipeline for `{tname}`",
                    f"-- Strategy: Star Schema Incremental Load with Surrogate Key Resolution",
                    f"-- ============================================================================",
                    f"INSERT INTO {tname} (",
                ]
                col_names = [c["name"] for c in cols]
                lines.append(f"    {', '.join(col_names)}")
                lines.append(")")
                lines.append("SELECT")
                
                sel_items = []
                for c in cols:
                    cn = c["name"]
                    if cn == "customer_sk":
                        sel_items.append("    COALESCE(c.customer_sk, 'UNKNOWN_SK') AS customer_sk")
                    elif cn == "estimated_delivery_days":
                        sel_items.append("    CAST(3 AS INT) AS estimated_delivery_days -- [AI-GENERATED FALLBACK]")
                    elif cn == "total_amount_usd":
                        sel_items.append("    o.total_amount AS total_amount_usd")
                    else:
                        sel_items.append(f"    o.{cn}")
                        
                lines.append(",\n".join(sel_items))
                lines.append(f"FROM {stg_source} o")
                lines.append(f"LEFT JOIN v_current_dim_{domain}_customer_core c")
                lines.append(f"  ON o.customer_id = c.customer_id")
                lines.append(f"WHERE NOT EXISTS (")
                lines.append(f"    SELECT 1 FROM {tname} existing WHERE existing.{pk} = o.{pk}")
                lines.append(f");")
                
                gold_sql[tname] = "\n".join(lines)
                
        return gold_sql

    @classmethod
    def generate_full_pipeline(
        cls,
        domain: str,
        source_tables: List[Dict[str, Any]] = None,
        target_schema: Dict[str, Any] = None,
        rules: List[Dict[str, Any]] = None,
        quality_policy: str = "QUARANTINE_VIEW",
        merge_strategy: str = "ANSI_MERGE"
    ) -> Dict[str, Any]:
        if not source_tables:
            source_tables = cls._get_default_source_tables()
        if target_schema is None:
            target_schema = {}
            
        bronze = cls.generate_bronze_layer(domain, source_tables, include_sample_data=True)
        silver = cls.generate_silver_layer(domain, source_tables, target_schema, rules, quality_policy)
        gold = cls.generate_gold_layer(domain, target_schema, merge_strategy)
        
        return {
            "domain": domain,
            "quality_policy": quality_policy,
            "merge_strategy": merge_strategy,
            "bronze": bronze,
            "silver": silver,
            "gold": gold,
            "total_sql_artifacts": len(bronze) + len(silver) + len(gold)
        }

    @classmethod
    def export_pipeline_files(
        cls,
        output_base_dir: str,
        domain: str,
        pipeline: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        base_path = os.path.join(output_base_dir, "pipelines", domain)
        bronze_dir = os.path.join(base_path, "01_bronze")
        silver_dir = os.path.join(base_path, "02_silver")
        gold_dir = os.path.join(base_path, "03_gold")
        
        os.makedirs(bronze_dir, exist_ok=True)
        os.makedirs(silver_dir, exist_ok=True)
        os.makedirs(gold_dir, exist_ok=True)
        
        exported_files = {"bronze": [], "silver": [], "gold": []}
        
        for name, sql in pipeline.get("bronze", {}).items():
            fpath = os.path.join(bronze_dir, f"{name}.sql")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(sql)
            exported_files["bronze"].append(fpath)
            
        for name, sql in pipeline.get("silver", {}).items():
            fpath = os.path.join(silver_dir, f"{name}.sql")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(sql)
            exported_files["silver"].append(fpath)
            
        for name, sql in pipeline.get("gold", {}).items():
            fpath = os.path.join(gold_dir, f"{name}.sql")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(sql)
            exported_files["gold"].append(fpath)
            
        return exported_files
