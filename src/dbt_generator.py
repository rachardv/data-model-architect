import os
from typing import Dict, Any, List, Optional

class DBTProjectGenerator:
    """
    Autonomous Enterprise dbt Core Project Generator.
    Compiles data architecture schemas into production-ready dbt-core repositories:
      - dbt_project.yml
      - models/staging/sources.yml & stg_*.sql
      - models/marts/dim_*.sql & fact_*.sql (with {{ ref(...) }})
      - models/schema.yml (with unique, not_null, and relationships tests)
    """

    @classmethod
    def generate_dbt_project_yaml(cls, domain: str) -> str:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        return f"""name: 'data_model_{clean_domain}'
version: '1.0.0'
config-version: 2

profile: 'default'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

models:
  data_model_{clean_domain}:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
"""

    @classmethod
    def generate_packages_yaml(cls) -> str:
        return """packages:
  - package: dbt-labs/dbt_project_evaluator
    version: 0.9.0
"""


    @classmethod
    def generate_sources_yaml(cls, domain: str, source_tables: List[Dict[str, Any]]) -> str:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        lines = [
            "version: 2",
            "",
            "sources:",
            f"  - name: raw",
            f"    schema: raw_{clean_domain}",
            f"    description: 'Raw ingested source tables for {clean_domain}'",
            "    tables:"
        ]
        
        for src in source_tables:
            tname = src.get("table_name", "source_table").lower()
            lines.append(f"      - name: {tname}")
            lines.append(f"        description: 'Raw landing table for {tname}'")
            cols = src.get("columns", [])
            if cols:
                lines.append("        columns:")
                for c in cols:
                    lines.append(f"          - name: {c['name']}")
                    if c.get("type"):
                        lines.append(f"            description: 'Datatype: {c['type']}'")
        return "\n".join(lines) + "\n"

    @classmethod
    def generate_staging_models(cls, domain: str, source_tables: List[Dict[str, Any]]) -> Dict[str, str]:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        staging_models = {}
        
        for src in source_tables:
            tname = src.get("table_name", "source_table").lower()
            model_name = f"stg_{clean_domain}_{tname}"
            cols = src.get("columns", [])
            col_lines = []
            for c in cols:
                cname = c["name"]
                ctype = c.get("type", "VARCHAR").upper()
                if "VARCHAR" in ctype or "TEXT" in ctype:
                    col_lines.append(f"        TRIM({cname}) AS {cname}")
                elif "INT" in ctype:
                    col_lines.append(f"        CAST({cname} AS BIGINT) AS {cname}")
                elif "DECIMAL" in ctype or "NUMERIC" in ctype:
                    col_lines.append(f"        CAST({cname} AS DECIMAL(14,2)) AS {cname}")
                elif "TIME" in ctype or "DATE" in ctype:
                    col_lines.append(f"        CAST({cname} AS TIMESTAMPTZ) AS {cname}")
                else:
                    col_lines.append(f"        {cname}")
                    
            select_cols = ",\n".join(col_lines) if col_lines else "        *"
            
            sql = f"""WITH source AS (
    SELECT * FROM {{{{ source('raw', '{tname}') }}}}
),
renamed AS (
    SELECT
{select_cols},
        CURRENT_TIMESTAMP AS _dbt_loaded_at
    FROM source
)
SELECT * FROM renamed
"""
            staging_models[model_name] = sql
            
        return staging_models

    @classmethod
    def generate_marts_models(cls, domain: str, target_schema: Dict[str, Any]) -> Dict[str, str]:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        marts_models = {}
        tables = target_schema.get("tables", [])
        
        for table in tables:
            tname = table.get("name", "").lower()
            ttype = table.get("type", "TABLE").upper()
            cols = table.get("columns", [])
            pk = table.get("primary_key", "")
            
            if ttype in ["DIMENSION", "DIM"]:
                # Dimension Mart Model
                src_entity = tname.replace(f"dim_{clean_domain}_", "").replace("_core", "")
                stg_ref = f"stg_{clean_domain}_{src_entity}s" if not src_entity.endswith("s") else f"stg_{clean_domain}_{src_entity}"
                
                col_selects = []
                for c in cols:
                    cname = c["name"]
                    if cname == pk:
                        col_selects.append(f"        -- Surrogate Key\n        ROW_NUMBER() OVER (ORDER BY {src_entity}_id) AS {cname}")
                    elif cname in ["scd_valid_from"]:
                        col_selects.append(f"        COALESCE(updated_at, CURRENT_TIMESTAMP) AS {cname}")
                    elif cname in ["scd_valid_to"]:
                        col_selects.append(f"        CAST('9999-12-31 23:59:59' AS TIMESTAMPTZ) AS {cname}")
                    elif cname in ["is_current"]:
                        col_selects.append(f"        TRUE AS {cname}")
                    else:
                        col_selects.append(f"        {cname}")
                        
                col_selects_str = ",\n".join(col_selects)
                sql = f"""WITH source AS (
    SELECT * FROM {{{{ ref('{stg_ref}') }}}}
),
final AS (
    SELECT
{col_selects_str}
    FROM source
)
SELECT * FROM final
"""
                marts_models[tname] = sql

            elif ttype in ["FACT", "FACTLESS_FACT"]:
                # Fact Mart Model
                dim_joins = []
                dim_refs = []
                for t in tables:
                    if t.get("type") in ["DIMENSION", "DIM"]:
                        dim_name = t.get("name", "").lower()
                        dim_entity = dim_name.replace(f"dim_{clean_domain}_", "").replace("_core", "")
                        dim_refs.append((dim_name, dim_entity))
                        
                join_clauses = []
                for dname, dentity in dim_refs:
                    join_clauses.append(
                        f"LEFT JOIN {{{{ ref('{dname}') }}}} {dentity[0]}\n"
                        f"  ON src.{dentity}_id = {dentity[0]}.{dentity}_id"
                    )
                    
                sel_items = []
                for c in cols:
                    cname = c["name"]
                    if cname.endswith("_sk") and not cname == pk:
                        ref_entity = cname.replace("_sk", "")
                        sel_items.append(f"    COALESCE({ref_entity[0]}.{cname}, -1) AS {cname}")
                    else:
                        sel_items.append(f"    src.{cname}")
                        
                stg_order_ref = f"stg_{clean_domain}_orders"
                joins_str = "\n".join(join_clauses)
                if joins_str:
                    joins_str = "\n" + joins_str
                    
                sel_items_str = ",\n".join(sel_items)
                sql = f"""WITH src AS (
    SELECT * FROM {{{{ ref('{stg_order_ref}') }}}}
)
SELECT
{sel_items_str}
FROM src{joins_str}
"""
                marts_models[tname] = sql

        return marts_models

    @classmethod
    def generate_schema_tests_yaml(cls, domain: str, target_schema: Dict[str, Any]) -> str:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        lines = [
            "version: 2",
            "",
            "models:"
        ]
        
        tables = target_schema.get("tables", [])
        for t in tables:
            tname = t.get("name", "")
            ttype = t.get("type", "TABLE")
            pk = t.get("primary_key", "")
            cols = t.get("columns", [])
            
            lines.append(f"  - name: {tname}")
            lines.append(f"    description: '{ttype} table for {clean_domain} enterprise data model'")
            lines.append("    columns:")
            
            for c in cols:
                cname = c["name"]
                is_pk = (cname == pk) or (cname in pk.split(", "))
                is_fk = cname.endswith("_sk") and not is_pk
                
                lines.append(f"      - name: {cname}")
                tests = []
                if is_pk:
                    tests.append("unique")
                    tests.append("not_null")
                elif is_fk:
                    tests.append("not_null")
                    # Try to infer target dimension for relationships test
                    target_dim = f"dim_{clean_domain}_{cname.replace('_sk', '')}_core"
                    # Check if target exists in tables
                    dim_match = next((tbl["name"] for tbl in tables if tbl["name"] == target_dim or tbl["name"] == f"dim_{clean_domain}_{cname.replace('_sk', '')}"), None)
                    if dim_match:
                        tests.append({
                            "relationships": {
                                "to": f"ref('{dim_match}')",
                                "field": cname
                            }
                        })
                elif not c.get("nullable", True):
                    tests.append("not_null")
                    
                if tests:
                    lines.append("        tests:")
                    for test in tests:
                        if isinstance(test, str):
                            lines.append(f"          - {test}")
                        elif isinstance(test, dict):
                            for tname_key, tparams in test.items():
                                lines.append(f"          - {tname_key}:")
                                for pkey, pval in tparams.items():
                                    lines.append(f"              {pkey}: {pval}")
                                    
        return "\n".join(lines) + "\n"

    @classmethod
    def generate_dbt_project(
        cls,
        domain: str,
        target_schema: Dict[str, Any],
        source_tables: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates full in-memory dbt project assets.
        """
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        if not source_tables:
            source_tables = [
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
            
        dbt_project_yaml = cls.generate_dbt_project_yaml(clean_domain)
        packages_yaml = cls.generate_packages_yaml()
        sources_yaml = cls.generate_sources_yaml(clean_domain, source_tables)
        staging_models = cls.generate_staging_models(clean_domain, source_tables)
        marts_models = cls.generate_marts_models(clean_domain, target_schema)
        schema_tests_yaml = cls.generate_schema_tests_yaml(clean_domain, target_schema)
        
        return {
            "domain": clean_domain,
            "dbt_project_yaml": dbt_project_yaml,
            "packages_yaml": packages_yaml,
            "sources_yaml": sources_yaml,
            "staging_models": staging_models,
            "marts_models": marts_models,
            "schema_tests_yaml": schema_tests_yaml,
            "total_models": len(staging_models) + len(marts_models)
        }

    @classmethod
    def export_dbt_project(
        cls,
        output_base_dir: str,
        domain: str,
        project_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Exports the in-memory dbt project directly into standard dbt folder structure:
          <output_base_dir>/dbt/<domain>/
            ├── dbt_project.yml
            ├── packages.yml
            └── models/
                ├── staging/
                │   ├── sources.yml
                │   └── stg_*.sql
                ├── marts/
                │   └── *.sql
                └── schema.yml
        """
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        dbt_root = os.path.join(output_base_dir, "dbt", clean_domain)
        staging_dir = os.path.join(dbt_root, "models", "staging")
        marts_dir = os.path.join(dbt_root, "models", "marts")
        
        os.makedirs(staging_dir, exist_ok=True)
        os.makedirs(marts_dir, exist_ok=True)
        
        exported_files = {
            "config": [],
            "staging": [],
            "marts": [],
            "tests": []
        }
        
        # 1. dbt_project.yml
        proj_path = os.path.join(dbt_root, "dbt_project.yml")
        with open(proj_path, "w", encoding="utf-8") as f:
            f.write(project_data["dbt_project_yaml"])
        exported_files["config"].append(proj_path)
        
        # 2. packages.yml (dbt-project-evaluator)
        if "packages_yaml" in project_data:
            pkg_path = os.path.join(dbt_root, "packages.yml")
            with open(pkg_path, "w", encoding="utf-8") as f:
                f.write(project_data["packages_yaml"])
            exported_files["config"].append(pkg_path)
            
        # 3. sources.yml
        src_path = os.path.join(staging_dir, "sources.yml")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(project_data["sources_yaml"])
        exported_files["staging"].append(src_path)
        
        # 4. Staging SQL models
        for name, sql in project_data.get("staging_models", {}).items():
            stg_path = os.path.join(staging_dir, f"{name}.sql")
            with open(stg_path, "w", encoding="utf-8") as f:
                f.write(sql)
            exported_files["staging"].append(stg_path)
            
        # 5. Marts SQL models
        for name, sql in project_data.get("marts_models", {}).items():
            mart_path = os.path.join(marts_dir, f"{name}.sql")
            with open(mart_path, "w", encoding="utf-8") as f:
                f.write(sql)
            exported_files["marts"].append(mart_path)
            
        # 6. schema.yml
        schema_path = os.path.join(dbt_root, "models", "schema.yml")
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(project_data["schema_tests_yaml"])
        exported_files["tests"].append(schema_path)
        
        return exported_files
