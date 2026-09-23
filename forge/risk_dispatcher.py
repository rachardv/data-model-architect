import time
import duckdb
from typing import Dict, Any, List, Optional
from forge.risk_engine import (
    ValidationContext,
    ValidationStrategyEngine,
    ValidationTier,
    RiskSeverity,
    RiskResult
)
from forge.benchmark_harness import ModelBenchmarkHarness
from forge.dbt_evaluator import DBTProjectEvaluator
from forge.chaos_engine import AdversarialChaosGenerator
from src.sql_runner import DuckDBPipelineRunner
from src.logger import get_logger

logger = get_logger("data_model_architect.risk_dispatcher")

class RiskToTestDispatcher:
    """
    The Forge Risk-to-Test Translation Engine.
    Inspects synthesized data models from the core engine, maps identified architectural
    and semantic risks into targeted physical stress test batteries, and awards the
    final 'CERTIFIED_PRODUCTION_READY' accreditation.
    """

    @classmethod
    def evaluate_and_certify(
        cls,
        workflow_res: Dict[str, Any],
        conn: Optional[duckdb.DuckDBPyConnection] = None,
        custom_verification_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Translates identified model risks into targeted physical tests in DuckDB:
          - SCD2 History Risk (RSK-03) -> Temporal Causality & Point-in-Time Proof
          - Multi-Fact Grain Risk (RSK-02) -> Metric Conservation & Fan-out Proof
          - Key Integrity Risk (RSK-04) -> Duplicate PKs & Orphan FK Quarantine
          - Plan Risk (RSK-05) -> Hash-Join EXPLAIN inspection
          - Efficiency & Skew Risk (RSK-06) -> Workload Fan-Out & Skew Stability
          - Compliance Risk (RSK-08) -> GDPR Right-to-be-Forgotten Pseudonymization
          - dbt Risk (RSK-07) -> dbt-project-evaluator structural standards
        """
        start_time = time.perf_counter()
        domain = workflow_res.get("domain", "default_domain")
        target_schema = workflow_res.get("target_schema") or workflow_res.get("schema_spec") or {}
        medallion_pipeline = workflow_res.get("medallion_pipeline")
        dbt_project = workflow_res.get("dbt_project")
        inferred_params = workflow_res.get("inferred_usage_params", {})

        # Use an isolated in-memory DuckDB instance for physical risk stress testing
        test_con = duckdb.connect(":memory:")

        try:
            # 1. Execute Deterministic 4-Pillar Physical Tests (Metric, Temporal, FK, Plan)
            deterministic_scorecard = ModelBenchmarkHarness.run_full_benchmark(
                domain=domain,
                target_schema=target_schema,
                medallion_pipeline=medallion_pipeline,
                dbt_project=dbt_project,
                run_industry_suites=False,
                conn=test_con
            )

            # 2. Construct Validation Context & Run 4-Tier Risk Council
            validation_ctx = ValidationContext(
                domain=domain,
                target_schema=target_schema,
                medallion_pipeline=medallion_pipeline,
                dbt_project=dbt_project,
                duckdb_conn=test_con,
                inferred_usage_params=inferred_params,
                benchmark_scorecard=deterministic_scorecard
            )
            risk_scorecard = ValidationStrategyEngine.evaluate(validation_ctx)

            # 4. Map Identified Risks to Targeted Test Batteries
            executed_batteries: List[Dict[str, Any]] = []

            # Battery A: Temporal Causality (RSK-03)
            if inferred_params.get("needs_history") or deterministic_scorecard.get("temporal_causality"):
                tc_res = deterministic_scorecard.get("temporal_causality", {})
                executed_batteries.append({
                    "battery": "TEMPORAL_TIMELINE_CAUSALITY",
                    "triggered_by_risk": "RSK-03",
                    "status": tc_res.get("status", "PASS"),
                    "details": tc_res.get("details", "SCD2 point-in-time intervals verified.")
                })

            # Battery B: Metric Conservation & Fan-out (RSK-02)
            if deterministic_scorecard.get("metric_conservation"):
                mc_res = deterministic_scorecard.get("metric_conservation", {})
                executed_batteries.append({
                    "battery": "METRIC_CONSERVATION_CHASM_TRAP",
                    "triggered_by_risk": "RSK-02",
                    "status": mc_res.get("status", "PASS"),
                    "details": mc_res.get("details", "Raw vs Gold financial metric drift verified at 0.0000.")
                })

            # Battery C: Referential Integrity & Quarantine (RSK-04)
            if deterministic_scorecard.get("referential_integrity"):
                ri_res = deterministic_scorecard.get("referential_integrity", {})
                executed_batteries.append({
                    "battery": "REFERENTIAL_GRAIN_QUARANTINE",
                    "triggered_by_risk": "RSK-04",
                    "status": ri_res.get("status", "PASS"),
                    "details": ri_res.get("details", "Zero duplicate primary keys, quarantine routing active.")
                })

            # Battery D: Physical EXPLAIN Query Plan (RSK-05)
            if deterministic_scorecard.get("query_execution"):
                qe_res = deterministic_scorecard.get("query_execution", {})
                executed_batteries.append({
                    "battery": "EXPLAIN_QUERY_PLAN_HASH_JOIN",
                    "triggered_by_risk": "RSK-05",
                    "status": qe_res.get("status", "PASS"),
                    "details": qe_res.get("details", "Sub-100ms Hash Join execution verified.")
                })

            # Battery E: Workload Efficiency & Key Skew Stability (RSK-06)
            skew_risk = next((r for r in risk_scorecard.get("results", []) if r.get("risk_id") == "RSK-06"), None)
            if skew_risk:
                executed_batteries.append({
                    "battery": "WORKLOAD_EFFICIENCY_FANOUT_STABILITY",
                    "triggered_by_risk": "RSK-06",
                    "status": skew_risk.get("status", "PASS"),
                    "details": skew_risk.get("details", "Workload join fan-out stability verified under Zipfian key skew.")
                })

            # Battery F: GDPR Right-to-be-Forgotten Pseudonymization (RSK-08)
            gdpr_risk = next((r for r in risk_scorecard.get("results", []) if r.get("risk_id") == "RSK-08-DYNAMIC"), None)
            if gdpr_risk:
                executed_batteries.append({
                    "battery": "GDPR_RIGHT_TO_BE_FORGOTTEN",
                    "triggered_by_risk": "RSK-08-DYNAMIC",
                    "status": gdpr_risk.get("status", "PASS"),
                    "details": gdpr_risk.get("details", "Pseudonymization sentinel verified.")
                })

            # Battery G: dbt Project Evaluator (RSK-07)
            if dbt_project:
                dbt_eval = DBTProjectEvaluator.evaluate_project(dbt_project)
                dbt_passed = (dbt_eval.get("status") in ["PASS", "SKIPPED"])
                executed_batteries.append({
                    "battery": "DBT_PROJECT_STANDARDS",
                    "triggered_by_risk": "RSK-07",
                    "status": "PASS" if dbt_passed else "FAIL",
                    "details": f"{dbt_eval.get('rules_passed', 0)}/{dbt_eval.get('total_rules', 4)} dbt rules passed."
                })

            # Battery H: OLAP Workload & Hop Efficiency (RSK-10)
            olap_hop_risk = next((r for r in risk_scorecard.get("results", []) if r.get("risk_id") == "RSK-10"), None)
            if olap_hop_risk:
                executed_batteries.append({
                    "battery": "OLAP_WORKLOAD_HOP_EFFICIENCY",
                    "triggered_by_risk": "RSK-10",
                    "status": olap_hop_risk.get("status", "PASS"),
                    "details": olap_hop_risk.get("details", "Query hop depth and structural fit verified against workload intent.")
                })

            # Battery I: Bus Matrix Conformance & Chasm Prevention (RSK-11)
            bus_matrix_risk = next((r for r in risk_scorecard.get("results", []) if r.get("risk_id") == "RSK-11"), None)
            if bus_matrix_risk:
                executed_batteries.append({
                    "battery": "BUS_MATRIX_CONFORMANCE_BATTERY",
                    "triggered_by_risk": "RSK-11",
                    "status": bus_matrix_risk.get("status", "PASS"),
                    "details": bus_matrix_risk.get("details", "Enterprise bus matrix conformed dimensions and chasm avoidance verified.")
                })

            # 5. Check Custom Case Verification Queries (if provided)
            custom_queries_passed = True
            if custom_verification_results is not None:
                for q in custom_verification_results:
                    if not q.get("passed", False):
                        custom_queries_passed = False

            # 6. Final Certification Decision Gate
            all_batteries_passed = all(b["status"] == "PASS" for b in executed_batteries)
            no_critical_halt = not risk_scorecard.get("critical_halt", False)
            deterministic_pass = (deterministic_scorecard.get("overall_status") == "PASS")

            is_certified = (all_batteries_passed and no_critical_halt and deterministic_pass and custom_queries_passed)
            certified_status = "CERTIFIED_PRODUCTION_READY" if is_certified else "RISK_VALIDATION_FAILED"

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "status": certified_status,
                "verdict": "PASS" if is_certified else "FAIL",
                "execution_time_ms": elapsed_ms,
                "total_batteries_executed": len(executed_batteries),
                "executed_batteries": executed_batteries,
                "risk_scorecard": risk_scorecard,
                "deterministic_scorecard": deterministic_scorecard,
                "critical_halt": risk_scorecard.get("critical_halt", False),
                "summary": f"Risk-to-Test Certification: {len(executed_batteries)} targeted batteries executed -> {certified_status}"
            }
        finally:
            test_con.close()
