import time
import json
import statistics
from typing import Dict, Any, List, Optional
from src.orchestration.captain import CaptainOrchestrator
from src.decision_engine import DataModelDecisionEngine
from src.noun_verb_parser import NounVerbSemanticParser
from src.semantic_benchmarks import BIRD_SPIDER_SCENARIOS
from src.logger import get_logger

logger = get_logger("data_model_architect.mega_benchmark")

class MegaBenchmarkRunner:
    """
    Academic & Enterprise Mega-Evaluation Suite.
    Stress-tests the full autonomous data modeling factory:
      1. Natural Language Intake & Semantic Vector Resolution
      2. Decision Matrix Pattern Classification
      3. Physical DDL & Medallion Pipeline Synthesis
      4. Enterprise dbt Core Project Generation
      5. Post-Generation Physical Verification in in-memory DuckDB:
         - Metric Conservation (Zero revenue inflation / no Chasm Trap)
         - Temporal Causality (SCD2 Point-in-Time non-overlapping intervals)
         - Referential & Grain Integrity (Unique PKs, zero orphan FKs)
         - Query Execution & Star Schema Join Plan Verification
         - dbt-project-evaluator Dimensional Standards
    """

    @classmethod
    def run_mega_benchmark(
        cls,
        total_cases: int = 5,
        export_path: Optional[str] = None,
        verbose: bool = True,
        end_to_end: bool = True
    ) -> Dict[str, Any]:
        """
        Executes parameterized benchmark evaluations across the enterprise domain catalog.
        
        Args:
            total_cases: Number of model scenarios to evaluate.
            export_path: Optional file path to export the complete JSON scorecard.
            verbose: If True, prints live progress and summary scorecards to stdout.
            end_to_end: If True (default), authors the full data model and executes the
                        5 post-generation physical verification pillars in DuckDB.
                        If False, executes high-throughput NLP classification testing.
        """
        mode_str = "End-to-End Model Generation & Physical Verification" if end_to_end else "Fast NLP Classification"
        if verbose:
            print(f"\n[*] Initiating Mega-Evaluation Suite: {total_cases} cases [{mode_str}]...")
            print("=" * 80)

        start_time = time.perf_counter()
        latencies_ms: List[float] = []
        domain_stats: Dict[str, Dict[str, int]] = {}
        case_results: List[Dict[str, Any]] = []
        passed_count = 0

        num_base_scenarios = len(BIRD_SPIDER_SCENARIOS)
        captain = CaptainOrchestrator() if end_to_end else None

        for i in range(total_cases):
            case_start = time.perf_counter()
            base = BIRD_SPIDER_SCENARIOS[i % num_base_scenarios]
            
            case_id = f"MEGA-{i+1:04d}-{base['id']}"
            domain = base["domain"]
            if domain not in domain_stats:
                domain_stats[domain] = {"total": 0, "passed": 0}
            domain_stats[domain]["total"] += 1

            # 1. Semantic Parameter Extraction
            enriched_narrative = f"{base['narrative']} {' '.join(base.get('business_answers', []))}"
            params = NounVerbSemanticParser.infer_parameters_from_business_narrative(enriched_narrative)
            
            if base.get("has_high_churn_ml_scores"):
                params["has_high_churn_ml_scores"] = True
            if base.get("has_recursive_hierarchy"):
                params["has_recursive_hierarchy"] = True
            if base.get("is_high_frequency_stream"):
                params["is_high_frequency_stream"] = True

            expected_pattern = base["expected_pattern"]

            if end_to_end:
                # -------------------------------------------------------------
                # TRUE END-TO-END MODEL SYNTHESIS & PHYSICAL DUCKDB VERIFICATION
                # -------------------------------------------------------------
                clean_domain = f"m_{i+1}_{domain[:10].lower().replace(' ', '_').replace('&', 'and').replace('-', '_')}"
                workflow_req = {
                    "domain": clean_domain,
                    "narrative": base["narrative"],
                    "business_answers": base.get("business_answers", []),
                    "usage_params": params,
                    "run_industry_suites": False  # Benchmark this specific generated model in DuckDB
                }
                
                model_output = captain.execute_workflow(workflow_req)
                classified_pattern = model_output.get("architecture_pattern")
                model_status = model_output.get("status")
                bench_scorecard = model_output.get("benchmark_scorecard", {})

                # Verify 5 Physical Post-Generation Pillars
                metric_status = bench_scorecard.get("metric_conservation", {}).get("status", "FAIL")
                temporal_status = bench_scorecard.get("temporal_causality", {}).get("status", "FAIL")
                ref_status = bench_scorecard.get("referential_integrity", {}).get("status", "FAIL")
                query_status = bench_scorecard.get("query_execution", {}).get("status", "FAIL")
                dbt_status = bench_scorecard.get("dbt_project_evaluator", {}).get("status", "SKIPPED")

                pattern_match = (classified_pattern == expected_pattern)
                physical_pass = (bench_scorecard.get("overall_status") == "PASS")
                model_certified = (model_status == "CERTIFIED_PRODUCTION_READY")

                is_pass = pattern_match and physical_pass and model_certified
                if is_pass:
                    passed_count += 1
                    domain_stats[domain]["passed"] += 1

                case_elapsed_ms = (time.perf_counter() - case_start) * 1000
                latencies_ms.append(case_elapsed_ms)

                case_result = {
                    "case_index": i + 1,
                    "case_id": case_id,
                    "domain": domain,
                    "benchmark": base["benchmark"],
                    "expected_pattern": expected_pattern,
                    "classified_pattern": classified_pattern,
                    "model_status": model_status,
                    "pillars": {
                        "metric_conservation": metric_status,
                        "temporal_causality": temporal_status,
                        "referential_integrity": ref_status,
                        "query_execution": query_status,
                        "dbt_evaluation": dbt_status
                    },
                    "benchmark_score": bench_scorecard.get("overall_score", 0.0),
                    "status": "PASS" if is_pass else "FAIL",
                    "latency_ms": round(case_elapsed_ms, 2)
                }
                case_results.append(case_result)

                if verbose:
                    p_icon = "PASS" if is_pass else "FAIL"
                    pillars_summary = f"M:{metric_status[0]} T:{temporal_status[0]} R:{ref_status[0]} Q:{query_status[0]} D:{dbt_status[0]}"
                    print(f"  [{i+1:>3}/{total_cases}] {p_icon} | {case_id:<26} | Pattern: {classified_pattern:<28} | [{pillars_summary}] | {case_elapsed_ms:>6.1f}ms")

            else:
                # -------------------------------------------------------------
                # HIGH-THROUGHPUT NLP CLASSIFICATION BENCHMARK
                # -------------------------------------------------------------
                decision = DataModelDecisionEngine.classify_architecture(**params)
                classified_pattern = decision.get("pattern")
                is_pass = (classified_pattern == expected_pattern)

                if is_pass:
                    passed_count += 1
                    domain_stats[domain]["passed"] += 1

                case_elapsed_ms = (time.perf_counter() - case_start) * 1000
                latencies_ms.append(case_elapsed_ms)

                case_results.append({
                    "case_index": i + 1,
                    "case_id": case_id,
                    "domain": domain,
                    "benchmark": base["benchmark"],
                    "expected_pattern": expected_pattern,
                    "classified_pattern": classified_pattern,
                    "status": "PASS" if is_pass else "FAIL",
                    "latency_ms": round(case_elapsed_ms, 3)
                })

                if verbose and ((i + 1) % 25 == 0 or (i + 1) == total_cases):
                    pct = ((i + 1) / total_cases) * 100
                    current_acc = (passed_count / (i + 1)) * 100
                    print(f"  [{i+1:>4}/{total_cases}] ({pct:>5.1f}%) | Accuracy: {current_acc:>5.1f}% | Avg Latency: {statistics.mean(latencies_ms):.2f}ms")

        total_elapsed = time.perf_counter() - start_time
        accuracy_pct = round((passed_count / total_cases) * 100.0, 2)
        
        sorted_lat = sorted(latencies_ms)
        p50 = statistics.median(sorted_lat)
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if len(sorted_lat) >= 20 else sorted_lat[-1]
        p99 = sorted_lat[int(len(sorted_lat) * 0.99)] if len(sorted_lat) >= 100 else sorted_lat[-1]

        report = {
            "title": f"Option C: Mega-Evaluation Report ({mode_str})",
            "mode": "END_TO_END_MODEL_GENERATION" if end_to_end else "FAST_NLP_CLASSIFICATION",
            "total_cases_evaluated": total_cases,
            "cases_passed": passed_count,
            "cases_failed": total_cases - passed_count,
            "overall_accuracy_pct": accuracy_pct,
            "overall_status": "PASS" if accuracy_pct >= 95.0 else "FAIL",
            "total_execution_time_seconds": round(total_elapsed, 3),
            "throughput_cases_per_sec": round(total_cases / total_elapsed, 1),
            "latency_metrics_ms": {
                "mean": round(statistics.mean(latencies_ms), 2),
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2)
            },
            "domain_accuracy_matrix": {
                dom: {
                    "total": d["total"],
                    "passed": d["passed"],
                    "accuracy_pct": round((d["passed"] / d["total"]) * 100.0, 1)
                }
                for dom, d in sorted(domain_stats.items())
            },
            "sample_cases": case_results[:10]
        }

        if verbose:
            cls._print_summary_card(report, end_to_end)

        if export_path:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            if verbose:
                print(f"\n[REPORT] Report successfully exported to: {export_path}")

        return report

    @classmethod
    def _print_summary_card(cls, report: Dict[str, Any], end_to_end: bool) -> None:
        print("\n" + "=" * 80)
        print("=== MEGA-EVALUATION SCORECARD: FULL FACTORY BENCHMARK ===")
        print("=" * 80)
        print(f"Evaluation Mode:   {report['mode']}")
        print(f"Overall Status:    {report['overall_status']} ({report['cases_passed']}/{report['total_cases_evaluated']} passed)")
        print(f"Overall Accuracy:  {report['overall_accuracy_pct']}%")
        print(f"Total Time:        {report['total_execution_time_seconds']}s ({report['throughput_cases_per_sec']} models/sec)")
        print(f"Latency Profile:   Mean={report['latency_metrics_ms']['mean']}ms | p50={report['latency_metrics_ms']['p50']}ms | p95={report['latency_metrics_ms']['p95']}ms | p99={report['latency_metrics_ms']['p99']}ms")
        if end_to_end:
            print("Physical Pillars:  [M]etric Conservation, [T]emporal Causality, [R]eferential, [Q]uery Plan, [D]bt Eval")
        print("-" * 80)
        print(f"{'Domain':<42} | {'Models':<6} | {'Accuracy':<8}")
        print("-" * 80)
        for dom, stats in sorted(report["domain_accuracy_matrix"].items()):
            print(f"{dom:<42} | {stats['total']:<6} | {stats['accuracy_pct']:>6.1f}%")
        print("=" * 80)
