import os
import logging
from typing import Dict, Any, List, Optional
import sqlglot
from sqlglot import exp, parse, transpile

logger = logging.getLogger(__name__)

class SQLDialectTranspiler:
    """
    AST SQL Transpilation and Validation Engine powered by SQLGlot.
    Enables zero-drift translation of ANSI/DuckDB Medallion SQL models
    into Snowflake, BigQuery, Databricks, PostgreSQL, and other target warehouses.
    """
    
    SUPPORTED_DIALECTS = ["duckdb", "snowflake", "bigquery", "postgres", "databricks"]
    
    @classmethod
    def transpile_sql(
        cls,
        sql: str,
        read_dialect: str = "duckdb",
        write_dialect: str = "snowflake",
        pretty: bool = True
    ) -> str:
        """
        Transpiles single or multi-statement SQL text between dialects.
        Preserves comment blocks and normalizes formatting.
        """
        read_d = read_dialect.lower()
        write_d = write_dialect.lower()
        
        if read_d == write_d:
            return sql
            
        try:
            parsed_expressions = parse(sql, read=read_d)
            transpiled_statements = []
            
            for expr in parsed_expressions:
                if expr is not None:
                    transpiled_statements.append(expr.sql(dialect=write_d, pretty=pretty))
                    
            return ";\n\n".join(transpiled_statements) + (";" if transpiled_statements else "")
        except Exception as e:
            logger.warning(
                "SQLGlot transpile warning from '%s' to '%s': %s. Falling back to native transpile.",
                read_dialect, write_dialect, e
            )
            try:
                results = transpile(sql, read=read_d, write=write_d, pretty=pretty)
                return ";\n\n".join(results) + (";" if results else "")
            except Exception as inner_e:
                logger.error("SQLGlot failed to transpile SQL block: %s", inner_e)
                return sql

    @classmethod
    def validate_ast(cls, sql: str, dialect: str = "duckdb") -> Dict[str, Any]:
        """
        Parses SQL AST and returns syntactic health, referenced tables, and structural metrics.
        """
        dialect = dialect.lower()
        try:
            statements = parse(sql, read=dialect)
            if not statements:
                return {
                    "is_valid": False,
                    "statement_count": 0,
                    "error": "No valid SQL statements found in input text",
                    "tables_referenced": [],
                    "has_joins": False
                }
                
            statement_types = []
            tables = set()
            has_joins = False
            
            for stmt in statements:
                if stmt is None:
                    continue
                statement_types.append(stmt.key.upper() if hasattr(stmt, "key") else "STATEMENT")
                
                for table_expr in stmt.find_all(exp.Table):
                    tbl_name = table_expr.name
                    if tbl_name:
                        tables.add(tbl_name.lower())
                        
                if any(stmt.find_all(exp.Join)):
                    has_joins = True
                    
            return {
                "is_valid": True,
                "statement_count": len(statements),
                "statement_types": statement_types,
                "tables_referenced": sorted(list(tables)),
                "has_joins": has_joins,
                "error": None
            }
        except Exception as e:
            return {
                "is_valid": False,
                "statement_count": 0,
                "error": str(e),
                "tables_referenced": [],
                "has_joins": False
            }

    @classmethod
    def transpile_pipeline(
        cls,
        pipeline: Dict[str, Any],
        target_dialects: Optional[List[str]] = None,
        source_dialect: str = "duckdb"
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Transpiles an entire Medallion pipeline (bronze, silver, gold) across target dialects.
        Returns: {dialect: {"bronze": {filename: sql}, "silver": {...}, "gold": {...}}}
        """
        dialects = target_dialects or cls.SUPPORTED_DIALECTS
        transpiled_result = {}
        
        for d in dialects:
            d_lower = d.lower()
            transpiled_result[d_lower] = {
                "bronze": {},
                "silver": {},
                "gold": {}
            }
            
            for layer in ["bronze", "silver", "gold"]:
                layer_files = pipeline.get(layer, {})
                for filename, sql_content in layer_files.items():
                    if d_lower == source_dialect.lower():
                        transpiled_result[d_lower][layer][filename] = sql_content
                    else:
                        trans_sql = cls.transpile_sql(
                            sql=sql_content,
                            read_dialect=source_dialect,
                            write_dialect=d_lower
                        )
                        transpiled_result[d_lower][layer][filename] = trans_sql
                        
        return transpiled_result

    @classmethod
    def export_dialects(
        cls,
        domain: str,
        pipeline: Dict[str, Any],
        base_dir: str = "docs/pipelines",
        target_dialects: Optional[List[str]] = None,
        source_dialect: str = "duckdb"
    ) -> Dict[str, int]:
        """
        Persists transpiled multi-dialect SQL pipelines into directory structure:
        docs/pipelines/<domain>/dialects/<dialect>/[01_bronze, 02_silver, 03_gold]
        """
        dialects = target_dialects or cls.SUPPORTED_DIALECTS
        transpiled = cls.transpile_pipeline(pipeline, target_dialects=dialects, source_dialect=source_dialect)
        counts = {}
        
        for d, layers in transpiled.items():
            dialect_count = 0
            for layer_name, folder_prefix in [("bronze", "01_bronze"), ("silver", "02_silver"), ("gold", "03_gold")]:
                out_dir = os.path.join(base_dir, domain, "dialects", d, folder_prefix)
                os.makedirs(out_dir, exist_ok=True)
                
                for fname, sql_content in layers.get(layer_name, {}).items():
                    clean_fname = fname if fname.endswith(".sql") else f"{fname}.sql"
                    file_path = os.path.join(out_dir, clean_fname)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(sql_content)
                    dialect_count += 1
            counts[d] = dialect_count
            
        return counts
