import os
import json
import time
import tempfile
import duckdb
from typing import Dict, Any, List, Optional
from forge.benchmark_catalog import PredefinedBenchmarkCase, VerificationQuery, get_predefined_benchmark_catalog
from forge.decision_tracer import DecisionTracer
from src.orchestration.captain import CaptainOrchestrator
from src.sql_runner import DuckDBPipelineRunner
from src.logger import get_logger

logger = get_logger("predefined_benchmark_gate")

class PredefinedBenchmarkGate:
    """
    System-Level Predefined Benchmark Validation Gate (The Certification Battery).
    Evaluates enterprise test cases sequentially 1-by-1, boots isolated DuckDB instances,
    completely builds physical models, executes case verification SQL queries, audits all
    architectural decisions, and cleanly overwrites deployment traces.
    """

    def __init__(self, trace_dir: str = "docs/benchmarks/traces", output_dir: Optional[str] = None):
        self.trace_dir = trace_dir
        self.output_dir = output_dir

    def run_case(self, case: PredefinedBenchmarkCase) -> Dict[str, Any]:
        """
        Evaluates a single predefined benchmark case 1-by-1 in an isolated in-memory DuckDB environment.
        """
        logger.info(f"Evaluating Predefined Benchmark Case 1-by-1: [{case.case_id}] {case.name}")
        tracer = DecisionTracer(
            case_id=case.case_id,
            domain=case.domain,
            name=case.name,
            hazard_category=case.hazard_category,
            is_intentional_trap=case.is_intentional_trap,
            prompt=case.prompt,
            expected_status=case.expected_status,
            citation=case.citation
        )

        case_db = duckdb.connect(":memory:")
        start_time = time.perf_counter()
        
        try:
            # 1. Execute Captain Workflow with Case Payload
            captain = CaptainOrchestrator(output_dir=self.output_dir)
            payload = {
                "domain": case.domain,
                "branch": "NEW_MODEL",
                "narrative": case.prompt,
                "business_answers": case.business_answers,
                "usage_params": case.usage_params,
                "baseline_vectors": case.baseline_vectors,
                "architectural_choice": case.architectural_choice
            }
            if case.rules is not None:
                payload["rules"] = case.rules
            if case.schema_spec is not None:
                payload["schema_spec"] = case.schema_spec
            
            workflow_res = captain.execute_workflow(payload)
            final_status = workflow_res.get("status", "WORKFLOW_HALTED")
            
            # 2. Record Decisions in Tracer
            tracer.record_intake(workflow_res)
            tracer.record_architecture(workflow_res)
            
            target_schema = workflow_res.get("target_schema")
            if not target_schema and "schema_spec" in payload and payload["schema_spec"]:
                target_schema = payload["schema_spec"]
            elif not target_schema and "tables" in workflow_res:
                target_schema = {"domain": case.domain, "tables": workflow_res.get("tables", [])}
                
            if target_schema:
                tracer.record_schema(target_schema)
                


            # 3. Physical Model Execution & Verification Queries
            medallion_pipeline = workflow_res.get("medallion_pipeline")
            if target_schema and medallion_pipeline:
                try:
                    DuckDBPipelineRunner.execute_and_verify(
                        domain=case.domain,
                        target_schema=target_schema,
                        pipeline=medallion_pipeline,
                        conn=case_db
                    )
                except Exception as e:
                    logger.warning(f"Pipeline pre-execution in case_db encountered: {e}")

            # 4. Inject Optional Benchmark Seed Data (SQL, inline records, or external files)
            self._inject_seed_data(case_db, case)

            # 5. Evaluate Custom Verification Queries against DuckDB
            custom_query_results = []
            for vq in case.verification_queries:
                q_start = time.perf_counter()
                actual_val = None
                passed = False
                err_msg = None
                
                try:
                    res = case_db.execute(vq.query).fetchall()
                    q_duration = (time.perf_counter() - q_start) * 1000
                    
                    if vq.assertion_type in ["scalar_eq", "scalar_gt", "scalar_gte", "scalar_lt", "scalar_lte", "zero_drift", "not_null"]:
                        actual_val = res[0][0] if (res and len(res) > 0 and len(res[0]) > 0) else None
                        
                        if vq.assertion_type == "scalar_eq":
                            passed = (actual_val == vq.expected_value)
                        elif vq.assertion_type == "scalar_gt":
                            passed = (actual_val is not None and actual_val > vq.expected_value)
                        elif vq.assertion_type == "scalar_gte":
                            passed = (actual_val is not None and actual_val >= vq.expected_value)
                        elif vq.assertion_type == "scalar_lt":
                            passed = (actual_val is not None and actual_val < vq.expected_value)
                        elif vq.assertion_type == "scalar_lte":
                            passed = (actual_val is not None and actual_val <= vq.expected_value)
                        elif vq.assertion_type == "zero_drift":
                            passed = (actual_val == 0 or (actual_val is not None and abs(float(actual_val)) < 0.0001))
                        elif vq.assertion_type == "not_null":
                            passed = (actual_val is not None)
                    elif vq.assertion_type == "row_count_gt":
                        actual_val = len(res)
                        passed = (actual_val > vq.expected_value)
                    elif vq.assertion_type == "row_count_eq":
                        actual_val = len(res)
                        passed = (actual_val == vq.expected_value)
                    elif vq.assertion_type == "is_empty":
                        actual_val = len(res)
                        passed = (actual_val == 0)
                    else:
                        actual_val = res
                        passed = True
                except Exception as e:
                    q_duration = (time.perf_counter() - q_start) * 1000
                    err_msg = str(e)
                    passed = False

                custom_query_results.append({"name": vq.name, "passed": passed})
                tracer.record_query_verification(
                    name=vq.name,
                    query=vq.query,
                    assertion_type=vq.assertion_type,
                    expected_value=vq.expected_value,
                    actual_value=actual_val,
                    passed=passed,
                    latency_ms=q_duration,
                    error=err_msg
                )

            # 6. Forge Risk-to-Test Translation & Certification Gate
            if final_status == "SYNTHESIZED_SUCCESSFULLY":
                from forge.risk_dispatcher import RiskToTestDispatcher
                cert_result = RiskToTestDispatcher.evaluate_and_certify(
                    workflow_res=workflow_res,
                    conn=case_db,
                    custom_verification_results=custom_query_results
                )
                final_status = cert_result["status"]
                tracer.record_validation(
                    validation_risk_scorecard=cert_result.get("risk_scorecard", {}),
                    benchmark_scorecard=cert_result.get("deterministic_scorecard")
                )

            tracer.finalize(final_status=final_status)
            saved_paths = tracer.save(self.trace_dir)

            return {
                "case_id": case.case_id,
                "domain": case.domain,
                "name": case.name,
                "hazard_category": case.hazard_category,
                "is_intentional_trap": case.is_intentional_trap,
                "expected_status": case.expected_status,
                "final_status": final_status,
                "verdict": tracer.trace.verdict,
                "execution_time_ms": tracer.trace.execution_time_ms,
                "queries_executed": len(case.verification_queries),
                "queries_passed": sum(1 for q in tracer.trace.verification_queries_trace if q.passed),
                "trace_files": saved_paths,
                "schema_decisions": tracer.trace.schema_decisions,
                "queries_trace": [q.model_dump() for q in tracer.trace.verification_queries_trace]
            }

        finally:
            case_db.close()

    def run_all_cases(self, catalog: Optional[List[PredefinedBenchmarkCase]] = None) -> Dict[str, Any]:
        """
        Sequentially executes all predefined benchmark cases 1-by-1.
        Returns an aggregated scorecard.
        """
        if catalog is not None:
            cases_to_run = catalog
        else:
            cases_to_run = get_predefined_benchmark_catalog()
            if not cases_to_run and os.path.exists("benchmarks/catalog"):
                from forge.catalog_loader import BenchmarkCatalogLoader
                BenchmarkCatalogLoader.load_from_directory("benchmarks/catalog", register=True)
                cases_to_run = get_predefined_benchmark_catalog()
        
        if not cases_to_run:
            logger.info("Predefined benchmark catalog is currently empty. Zero cases executed.")
            return {
                "status": "EMPTY_CATALOG",
                "message": "Predefined benchmark catalog is empty. Register test cases to evaluate.",
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate_pct": 100.0,
                "trap_defenses_tested": 0,
                "trap_defenses_passed": 0,
                "execution_time_ms": 0.0,
                "cases": []
            }

        logger.info(f"Starting Predefined Benchmark Gate across {len(cases_to_run)} cases (1-by-1 sequential)")
        start_time = time.perf_counter()
        results = []

        for case in cases_to_run:
            case_result = self.run_case(case)
            results.append(case_result)

        total = len(results)
        passed = sum(1 for r in results if r["verdict"] == "PASS")
        failed = total - passed
        pass_rate = (passed / total) * 100.0 if total > 0 else 100.0

        traps_tested = sum(1 for r in results if r["is_intentional_trap"])
        traps_passed = sum(1 for r in results if r["is_intentional_trap"] and r["verdict"] == "PASS")

        overall_status = "PASS" if failed == 0 else "FAIL"
        total_time = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "status": overall_status,
            "total_cases": total,
            "passed_cases": passed,
            "failed_cases": failed,
            "pass_rate_pct": round(pass_rate, 1),
            "trap_defenses_tested": traps_tested,
            "trap_defenses_passed": traps_passed,
            "execution_time_ms": total_time,
            "cases": results
        }

    def _inject_seed_data(self, conn: duckdb.DuckDBPyConnection, case: PredefinedBenchmarkCase) -> None:
        """
        Injects optional seed data into the DuckDB instance before executing verification queries.
        Supports:
          1. seed_sql: Raw SQL statements (DDL/DML).
          2. seed_data: Dictionary mapping table names to row records (list of dicts).
          3. seed_files: List of file paths to CSV or Parquet files.
        """
        # 1. Seed SQL
        if case.seed_sql:
            for stmt in case.seed_sql.split(";"):
                trimmed = stmt.strip()
                if trimmed:
                    try:
                        conn.execute(trimmed)
                    except Exception as e:
                        logger.warning(f"Error executing seed_sql for case [{case.case_id}]: {e}")

        # 2. Seed Data (inline dicts)
        if case.seed_data:
            existing_tables = set(r[0] for r in conn.execute("SHOW TABLES").fetchall())
            for tbl_name, rows in case.seed_data.items():
                if not rows:
                    continue
                tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
                try:
                    json.dump(rows, tf)
                    tf.close()
                    clean_path = tf.name.replace("\\", "/")
                    if tbl_name in existing_tables:
                        conn.execute(f"DELETE FROM {tbl_name}")
                        conn.execute(f"INSERT INTO {tbl_name} BY NAME SELECT * FROM read_json_auto('{clean_path}')")
                    else:
                        conn.execute(f"CREATE TABLE {tbl_name} AS SELECT * FROM read_json_auto('{clean_path}')")
                except Exception as e:
                    logger.warning(f"Error injecting seed_data for table '{tbl_name}' in case [{case.case_id}]: {e}")
                finally:
                    if os.path.exists(tf.name):
                        os.unlink(tf.name)

        # 3. Seed Files (CSV or Parquet)
        if case.seed_files:
            existing_tables = set(r[0] for r in conn.execute("SHOW TABLES").fetchall())
            for fpath in case.seed_files:
                resolved_path = fpath
                if not os.path.isabs(fpath) and case.source_file:
                    resolved_path = os.path.join(os.path.dirname(case.source_file), fpath)
                if not os.path.exists(resolved_path):
                    logger.warning(f"Seed file not found for case [{case.case_id}]: {fpath} (resolved: {resolved_path})")
                    continue
                tbl_name = os.path.splitext(os.path.basename(fpath))[0]
                clean_path = resolved_path.replace("\\", "/")
                try:
                    if fpath.lower().endswith(".csv"):
                        if tbl_name in existing_tables:
                            conn.execute(f"INSERT INTO {tbl_name} BY NAME SELECT * FROM read_csv_auto('{clean_path}')")
                        else:
                            conn.execute(f"CREATE TABLE {tbl_name} AS SELECT * FROM read_csv_auto('{clean_path}')")
                    elif fpath.lower().endswith((".parquet", ".pq")):
                        if tbl_name in existing_tables:
                            conn.execute(f"INSERT INTO {tbl_name} BY NAME SELECT * FROM read_parquet('{clean_path}')")
                        else:
                            conn.execute(f"CREATE TABLE {tbl_name} AS SELECT * FROM read_parquet('{clean_path}')")
                except Exception as e:
                    logger.warning(f"Error loading seed file '{fpath}' for case [{case.case_id}]: {e}")
