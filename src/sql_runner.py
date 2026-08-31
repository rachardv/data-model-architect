import duckdb
from typing import Dict, Any, List, Optional
from src.ddl_generator import ANSISQLGenerator

class DuckDBPipelineRunner:
    """
    In-Memory DuckDB SQL Pipeline Execution Engine.
    Executes and verifies generated Bronze DDL, Silver staging/quarantine views,
    and Gold dimensional/fact transformations end-to-end in an ephemeral DuckDB database.
    """

    @classmethod
    def _clean_and_split_statements(cls, sql: str) -> List[str]:
        clean_lines = []
        for line in sql.splitlines():
            trimmed = line.strip()
            if trimmed.startswith("--"):
                continue
            if "--" in line:
                line = line.split("--")[0].rstrip()
            clean_lines.append(line)
        clean_sql = "\n".join(clean_lines)
        return [stmt.strip() for stmt in clean_sql.split(";") if stmt.strip()]
    
    @classmethod
    def execute_and_verify(
        cls,
        domain: str,
        target_schema: Dict[str, Any],
        pipeline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes Bronze -> Silver -> Gold in an ephemeral in-memory DuckDB instance
        and returns a comprehensive verification report.
        """
        conn = duckdb.connect(":memory:")
        execution_log = []
        
        # 1. Execute Bronze DDL & Inserts
        bronze_results = {}
        for name, sql in pipeline.get("bronze", {}).items():
            statements = cls._clean_and_split_statements(sql)
            for stmt in statements:
                conn.execute(stmt)
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            bronze_results[name] = {"rows_inserted": count, "status": "SUCCESS"}
            execution_log.append(f"Bronze table {name} created with {count} rows")
            
        # 2. Execute Silver Staging & Quarantine Views
        silver_results = {}
        for name, sql in pipeline.get("silver", {}).items():
            statements = cls._clean_and_split_statements(sql)
            for stmt in statements:
                conn.execute(stmt)
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            silver_results[name] = {"view_rows": count, "status": "SUCCESS"}
            execution_log.append(f"Silver view {name} created ({count} rows)")
            
        # 3. Create Gold Target Tables (DDL)
        gold_results = {}
        tables = target_schema.get("tables", [])
        for t in tables:
            ddl = ANSISQLGenerator.generate_table_sql(
                table_name=t["name"],
                columns=t["columns"],
                primary_key=t["primary_key"]
            )
            statements = cls._clean_and_split_statements(ddl)
            for stmt in statements:
                conn.execute(stmt)
            execution_log.append(f"Gold table {t['name']} created")
            
        # 4. Execute Gold Transformation Scripts
        for name, sql in pipeline.get("gold", {}).items():
            statements = cls._clean_and_split_statements(sql)
            for stmt in statements:
                conn.execute(stmt)
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            gold_results[name] = {"final_rows": count, "status": "SUCCESS"}
            execution_log.append(f"Gold mart {name} loaded ({count} rows)")
            
        # 5. Verify Invariant Quarantine Performance
        quarantine_caught = 0
        quarantine_tables = [n for n in silver_results if "quarantine" in n]
        for q in quarantine_tables:
            q_rows = conn.execute(f"SELECT * FROM {q}").fetchall()
            quarantine_caught += len(q_rows)
            
        # Check active dimension view if present
        active_dim_views = [f"v_current_{t['name']}" for t in tables if t.get("type") == "DIMENSION"]
        active_counts = {}
        for adv in active_dim_views:
            try:
                ac = conn.execute(f"SELECT COUNT(*) FROM {adv}").fetchone()[0]
                active_counts[adv] = ac
            except Exception:
                pass
                
        conn.close()
        
        return {
            "status": "EXECUTION_VERIFIED",
            "domain": domain,
            "engine": f"DuckDB v{duckdb.__version__}",
            "bronze": bronze_results,
            "silver": silver_results,
            "gold": gold_results,
            "quarantine_records_isolated": quarantine_caught,
            "active_dimension_views": active_counts,
            "execution_log": execution_log
        }
