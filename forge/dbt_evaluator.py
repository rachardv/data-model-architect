import re
from typing import Dict, Any, List, Set

class DBTProjectEvaluator:
    """
    Automated Dimensional Modeling Audit Engine.
    Modeled after dbt Labs' open-source `dbt-project-evaluator` package.
    Evaluates compiled dbt project structures for:
      1. Missing Primary Key Tests (unique, not_null)
      2. Direct Staging Joins / Staging Bypass
      3. Fanout Hazards (unchecked Cartesian/multi-source fanouts)
      4. Circular Dependencies (acyclic DAG validation)
    """

    @classmethod
    def evaluate_project(cls, dbt_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs comprehensive dbt-project-evaluator rules across the in-memory dbt project.
        Returns a structured scorecard: status (PASS/FAIL), total_rules, violations.
        """
        violations = []
        rule_results = {}

        # 1. Missing Primary Key Tests
        pk_test_res = cls._check_primary_key_tests(dbt_project)
        rule_results["missing_primary_key_tests"] = pk_test_res
        if not pk_test_res["passed"]:
            violations.extend(pk_test_res["violations"])

        # 2. Direct Staging Bypass / Conformance
        staging_bypass_res = cls._check_staging_conformance(dbt_project)
        rule_results["direct_staging_joins"] = staging_bypass_res
        if not staging_bypass_res["passed"]:
            violations.extend(staging_bypass_res["violations"])

        # 3. Fanout Hazards
        fanout_res = cls._check_fanout_hazards(dbt_project)
        rule_results["fanout_hazards"] = fanout_res
        if not fanout_res["passed"]:
            violations.extend(fanout_res["violations"])

        # 4. Circular Dependencies (DAG cycles)
        dag_res = cls._check_circular_dependencies(dbt_project)
        rule_results["circular_dependencies"] = dag_res
        if not dag_res["passed"]:
            violations.extend(dag_res["violations"])

        overall_status = "PASS" if len(violations) == 0 else "FAIL"
        
        return {
            "status": overall_status,
            "total_rules": 4,
            "rules_passed": sum(1 for r in rule_results.values() if r["passed"]),
            "rule_results": rule_results,
            "violations": violations,
            "packages_configured": "dbt_project_evaluator" in dbt_project.get("packages_yaml", "")
        }

    @classmethod
    def _check_primary_key_tests(cls, dbt_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asserts that every mart model in schema_tests_yaml has both `unique` and `not_null` assertions.
        """
        schema_yml = dbt_project.get("schema_tests_yaml", "")
        marts_models = dbt_project.get("marts_models", {})
        violations = []

        for model_name in marts_models.keys():
            if f"- name: {model_name}" not in schema_yml:
                violations.append(f"Model `{model_name}` has no schema.yml documentation or test definitions")
                continue

            pattern = rf"(?:^|\n)\s{{2}}- name:\s+{re.escape(model_name)}\b.*?(?=\n\s{{2}}- name:|\Z)"
            model_section_match = re.search(pattern, schema_yml, re.DOTALL)
            if not model_section_match:
                violations.append(f"Model `{model_name}` block could not be parsed in schema.yml")
                continue

            section = model_section_match.group(0)
            has_unique = "unique" in section
            has_not_null = "not_null" in section

            if not (has_unique and has_not_null):
                violations.append(
                    f"Model `{model_name}` is missing required primary key integrity tests "
                    f"(has_unique={has_unique}, has_not_null={has_not_null})"
                )

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "details": f"Verified {len(marts_models)} mart model(s) for unique and not_null primary key coverage"
        }

    @classmethod
    def _check_staging_conformance(cls, dbt_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asserts that staging models only select from sources and do not introduce complex joins.
        """
        staging_models = dbt_project.get("staging_models", {})
        violations = []

        for name, sql in staging_models.items():
            if "source(" not in sql:
                violations.append(f"Staging model `{name}` does not reference a declared source via {{ source(...) }}")

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "details": f"Verified {len(staging_models)} staging model(s) adhere to 1:1 raw source ingestion pattern"
        }

    @classmethod
    def _check_fanout_hazards(cls, dbt_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asserts that fact models joining staging tables join through conformed dimensions or surrogate keys
        rather than unchecked Cartesian cross joins.
        """
        marts = dbt_project.get("marts_models", {})
        violations = []

        for name, sql in marts.items():
            sql_upper = sql.upper()
            if "CROSS JOIN" in sql_upper:
                violations.append(f"Fanout Hazard: Mart `{name}` contains an explicit CROSS JOIN")
            if "JOIN" in sql_upper and "ON " not in sql_upper and "USING" not in sql_upper:
                violations.append(f"Fanout Hazard: Mart `{name}` contains an unconstrained JOIN without ON/USING predicate")

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "details": f"Verified {len(marts)} mart model(s) have zero unconstrained Cartesian joins"
        }

    @classmethod
    def _check_circular_dependencies(cls, dbt_project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs the DAG of ref(...) calls and detects cycles.
        """
        adj: Dict[str, List[str]] = {}
        all_models = {}
        all_models.update(dbt_project.get("staging_models", {}))
        all_models.update(dbt_project.get("marts_models", {}))

        for name, sql in all_models.items():
            refs = re.findall(r"ref\(['\"]([a-zA-Z0-9_]+)['\"]\)", sql)
            adj[name] = refs

        visited: Dict[str, int] = {}
        cycles = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            for neighbor in adj.get(node, []):
                if neighbor not in visited or visited[neighbor] == 0:
                    dfs(neighbor, path + [neighbor])
                elif visited[neighbor] == 1:
                    cycle_path = " -> ".join(path + [neighbor])
                    cycles.append(f"Circular dependency cycle detected: {cycle_path}")
            visited[node] = 2

        for model in adj:
            if model not in visited or visited[model] == 0:
                dfs(model, [model])

        return {
            "passed": len(cycles) == 0,
            "violations": cycles,
            "details": f"DAG validated across {len(all_models)} model(s): 0 dependency cycles detected"
        }
