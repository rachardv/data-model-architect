from typing import List, Dict, Any

class ANSISQLGenerator:
    """
    Generates clean, portable, standard ANSI SQL DDL with explicit constraints
    and [AI-GENERATED] mockup tagging annotations.
    """
    
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
        lines.append(f"    CONSTRAINT pk_{table_name} PRIMARY KEY ({primary_key})")
        
        if foreign_keys:
            for fk in foreign_keys:
                lines.append(f"    CONSTRAINT fk_{table_name}_{fk['col']} FOREIGN KEY ({fk['col']}) REFERENCES {fk['ref_table']}({fk['ref_col']}),")
                
        if check_constraints:
            for i, chk in enumerate(check_constraints):
                lines.append(f"    CONSTRAINT chk_{table_name}_{i+1} CHECK ({chk}),")
                
        # Clean trailing commas
        sql = "\n".join(lines)
        if sql.endswith(","):
            sql = sql[:-1]
        sql += "\n);"
        return sql
