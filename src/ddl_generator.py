from typing import List, Dict, Any, Optional

class ANSISQLGenerator:
    """
    Generates clean, portable, standard ANSI SQL DDL with explicit constraints,
    Kimball Closure Bridge tables, Multi-Currency Fact Triads, and JSONB support.
    """
    
    SUPPORTED_TYPES = {
        "BIGINT", "INT", "INTEGER", "SMALLINT", "VARCHAR", "TEXT",
        "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "BOOLEAN", "DATE",
        "TIMESTAMP", "TIMESTAMPTZ", "JSONB", "VARIANT", "RECORD"
    }
    
    @staticmethod
    def generate_table_sql(
        table_name: str,
        columns: List[Dict[str, Any]],
        primary_key: str,
        foreign_keys: List[Dict[str, str]] = None,
        check_constraints: List[str] = None
    ) -> str:
        lines = [f"CREATE TABLE {table_name} ("]
        col_defs = []
        
        for col in columns:
            name = col["name"]
            dtype = col["type"]
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            default = f" DEFAULT {col['default']}" if "default" in col else ""
            tag = " -- [AI-GENERATED]" if col.get("is_inferred", False) else ""
            col_defs.append(f"    {name:<28} {dtype}{nullable}{default},{tag}")
            
        lines.extend(col_defs)
        pk_line = f"    CONSTRAINT pk_{table_name} PRIMARY KEY ({primary_key})"
        if foreign_keys or check_constraints:
            pk_line += ","
        lines.append(pk_line)
        
        if foreign_keys:
            for i, fk in enumerate(foreign_keys):
                has_next = (i < len(foreign_keys) - 1) or bool(check_constraints)
                comma = "," if has_next else ""
                lines.append(f"    CONSTRAINT fk_{table_name}_{fk['col']} FOREIGN KEY ({fk['col']}) REFERENCES {fk['ref_table']}({fk['ref_col']}){comma}")
                
        if check_constraints:
            for i, chk in enumerate(check_constraints):
                has_next = (i < len(check_constraints) - 1)
                comma = "," if has_next else ""
                lines.append(f"    CONSTRAINT chk_{table_name}_{i+1} CHECK ({chk}){comma}")
                
        sql = "\n".join(lines) + "\n);"
        return sql

    @staticmethod
    def generate_multi_currency_columns(measure_name: str = "amount", target_currency: str = "usd") -> List[Dict[str, Any]]:
        """
        Generates the standard Kimball Multi-Currency Fact Triad:
        1. Local transaction amount
        2. ISO-4217 Currency Code
        3. Spot exchange rate to target currency
        4. Standardized target currency amount
        """
        target = target_currency.lower()
        return [
            {"name": f"{measure_name}_local", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
            {"name": "currency_code", "type": "VARCHAR(3)", "nullable": False, "is_inferred": False},
            {"name": f"exchange_rate_to_{target}", "type": "DECIMAL(12,6)", "nullable": False, "is_inferred": False},
            {"name": f"{measure_name}_{target}", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False}
        ]

    @staticmethod
    def generate_closure_table_sql(entity_name: str, id_type: str = "BIGINT") -> str:
        """
        Generates a Kimball Transitive Closure Bridge Table for Bill of Materials (BOM)
        or recursive parent-child hierarchies (e.g. employee org charts, parts assemblies).
        """
        clean_name = entity_name.lower()
        columns = [
            {"name": f"ancestor_{clean_name}_id", "type": id_type, "nullable": False},
            {"name": f"descendant_{clean_name}_id", "type": id_type, "nullable": False},
            {"name": "depth_level", "type": "INT", "nullable": False},
            {"name": "is_leaf", "type": "BOOLEAN", "nullable": False, "default": "FALSE"}
        ]
        return ANSISQLGenerator.generate_table_sql(
            table_name=f"bridge_{clean_name}_closure",
            columns=columns,
            primary_key=f"ancestor_{clean_name}_id, descendant_{clean_name}_id",
            check_constraints=["depth_level >= 0"]
        )
