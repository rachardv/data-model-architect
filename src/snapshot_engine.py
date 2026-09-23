import os
import json
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from src.logger import get_logger

logger = get_logger("snapshot_engine")

def _normalize_json_val(val: Any) -> Any:
    """Recursively converts Decimal and non-primitive objects to JSON-friendly primitives."""
    if isinstance(val, Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, dict):
        return {k: _normalize_json_val(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_normalize_json_val(v) for v in val]
    return val

class GoldenSnapshotEngine:
    """
    Golden Snapshot & Regression Diffing Engine for Data Model Architect.
    Captures certified architectural fingerprints of benchmark test executions,
    detects silent schema drift, flags query latency regressions, and evaluates
    conformance against the golden baseline.
    """

    DEFAULT_SNAPSHOT_PATH = os.path.join("benchmarks", "baselines", "golden_snapshot.json")

    @classmethod
    def capture_snapshot(
        cls,
        case_results: List[Dict[str, Any]],
        output_path: str = DEFAULT_SNAPSHOT_PATH
    ) -> Dict[str, Any]:
        """
        Extracts structural and performance fingerprints from benchmark execution results
        and persists them as the certified golden baseline snapshot.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cases_snapshot: Dict[str, Any] = {}
        for r in case_results:
            case_id = r.get("case_id", "UNKNOWN")
            
            # Format tables dict
            tables_dict: Dict[str, Any] = {}
            for t in r.get("schema_decisions", []):
                t_name = t.get("table_name", "")
                if not t_name:
                    continue
                cols = t.get("columns", [])
                clean_cols = [c["name"] if isinstance(c, dict) else str(c) for c in cols]
                tables_dict[t_name] = {
                    "table_name": t_name,
                    "type": t.get("type", "UNKNOWN"),
                    "primary_key": t.get("primary_key", ""),
                    "columns": clean_cols
                }

            # Format queries list
            queries_list = []
            for q in r.get("queries_trace", []):
                queries_list.append({
                    "name": q.get("name"),
                    "assertion_type": q.get("assertion_type"),
                    "expected_value": _normalize_json_val(q.get("expected_value")),
                    "actual_value": _normalize_json_val(q.get("actual_value")),
                    "passed": q.get("passed", False),
                    "latency_ms": round(float(q.get("latency_ms", 0.0)), 2)
                })

            cases_snapshot[case_id] = {
                "case_id": case_id,
                "name": r.get("name", ""),
                "domain": r.get("domain", ""),
                "hazard_category": r.get("hazard_category", ""),
                "is_intentional_trap": r.get("is_intentional_trap", False),
                "expected_status": r.get("expected_status", ""),
                "observed_status": r.get("final_status", ""),
                "verdict": r.get("verdict", ""),
                "execution_time_ms": round(float(r.get("execution_time_ms", 0.0)), 2),
                "tables": tables_dict,
                "queries": queries_list
            }

        snapshot_payload = {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(cases_snapshot),
            "cases": cases_snapshot
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_payload, f, indent=2, default=lambda o: float(o) if isinstance(o, Decimal) else str(o))

        logger.info(f"Captured golden baseline snapshot across {len(cases_snapshot)} cases -> {output_path}")
        return snapshot_payload

    @classmethod
    def load_snapshot(cls, snapshot_path: str = DEFAULT_SNAPSHOT_PATH) -> Optional[Dict[str, Any]]:
        """
        Loads the golden baseline snapshot from disk. Returns None if file does not exist.
        """
        if not os.path.exists(snapshot_path):
            logger.warning(f"Golden baseline snapshot not found at: {snapshot_path}")
            return None

        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"Failed to parse golden baseline snapshot at '{snapshot_path}': {e}")
            raise ValueError(f"Corrupted golden baseline snapshot at '{snapshot_path}': {e}") from e

    @classmethod
    def compare_run_to_snapshot(
        cls,
        live_results: List[Dict[str, Any]],
        snapshot: Dict[str, Any],
        latency_threshold_pct: float = 100.0,
        min_latency_delta_ms: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compares live benchmark gate execution results against the certified golden baseline.
        Computes schema drift, status deviations, and latency regressions.
        """
        base_cases = snapshot.get("cases", {})
        diff_cases = []
        
        has_schema_drift = False
        has_status_drift = False
        has_latency_regression = False

        for live in live_results:
            cid = live.get("case_id", "UNKNOWN")
            base = base_cases.get(cid)

            case_diff = {
                "case_id": cid,
                "name": live.get("name", ""),
                "is_new_case": base is None,
                "status_match": True,
                "verdict_match": True,
                "schema_drift": False,
                "latency_regression": False,
                "details": []
            }

            if not base:
                case_diff["details"].append(f"New case [{cid}] not present in golden baseline.")
                diff_cases.append(case_diff)
                continue

            # 1. Status & Verdict Comparison
            live_status = live.get("final_status")
            base_status = base.get("observed_status")
            if live_status != base_status:
                case_diff["status_match"] = False
                has_status_drift = True
                case_diff["details"].append(f"Status changed: Baseline='{base_status}' -> Live='{live_status}'")

            live_verdict = live.get("verdict")
            base_verdict = base.get("verdict")
            if live_verdict != base_verdict:
                case_diff["verdict_match"] = False
                case_diff["details"].append(f"Verdict flipped: Baseline='{base_verdict}' -> Live='{live_verdict}'")

            # 2. Schema Drift Comparison
            live_tables: Dict[str, Any] = {}
            for t in live.get("schema_decisions", []):
                t_name = t.get("table_name", "")
                if t_name:
                    cols = t.get("columns", [])
                    clean_cols = [c["name"] if isinstance(c, dict) else str(c) for c in cols]
                    live_tables[t_name] = {
                        "primary_key": t.get("primary_key", ""),
                        "columns": set(clean_cols)
                    }

            base_tables: Dict[str, Any] = {}
            for t_name, t_val in base.get("tables", {}).items():
                base_tables[t_name] = {
                    "primary_key": t_val.get("primary_key", ""),
                    "columns": set(t_val.get("columns", []))
                }

            # Check removed / added tables
            removed_tables = set(base_tables.keys()) - set(live_tables.keys())
            added_tables = set(live_tables.keys()) - set(base_tables.keys())
            if removed_tables:
                case_diff["schema_drift"] = True
                has_schema_drift = True
                case_diff["details"].append(f"Table(s) REMOVED: {', '.join(sorted(removed_tables))}")
            if added_tables:
                case_diff["schema_drift"] = True
                has_schema_drift = True
                case_diff["details"].append(f"Table(s) ADDED: {', '.join(sorted(added_tables))}")

            # Check column drift in shared tables
            common_tables = set(live_tables.keys()) & set(base_tables.keys())
            for t_name in sorted(common_tables):
                lt = live_tables[t_name]
                bt = base_tables[t_name]
                
                dropped_cols = bt["columns"] - lt["columns"]
                added_cols = lt["columns"] - bt["columns"]
                if dropped_cols:
                    case_diff["schema_drift"] = True
                    has_schema_drift = True
                    case_diff["details"].append(f"Table '{t_name}' column(s) REMOVED: {', '.join(sorted(dropped_cols))}")
                if added_cols:
                    case_diff["schema_drift"] = True
                    has_schema_drift = True
                    case_diff["details"].append(f"Table '{t_name}' column(s) ADDED: {', '.join(sorted(added_cols))}")

                if lt["primary_key"] != bt["primary_key"]:
                    case_diff["schema_drift"] = True
                    has_schema_drift = True
                    case_diff["details"].append(f"Table '{t_name}' PK changed: '{bt['primary_key']}' -> '{lt['primary_key']}'")

            # 3. Query Assertions & Latency Comparison
            base_q_map = {q.get("name"): q for q in base.get("queries", []) if q.get("name")}
            for lq in live.get("queries_trace", []):
                q_name = lq.get("name")
                if not q_name or q_name not in base_q_map:
                    continue
                bq = base_q_map[q_name]

                # Check assertion flip
                if lq.get("passed") != bq.get("passed"):
                    case_diff["details"].append(f"Query '{q_name}' passed status flipped: {bq.get('passed')} -> {lq.get('passed')}")

                # Check latency regression (> threshold and >= min delta)
                live_lat = float(lq.get("latency_ms", 0.0))
                base_lat = float(bq.get("latency_ms", 0.0))
                delta_ms = live_lat - base_lat
                pct_increase = ((live_lat - base_lat) / base_lat * 100.0) if base_lat > 0.0 else 0.0

                if pct_increase > latency_threshold_pct and delta_ms >= min_latency_delta_ms:
                    case_diff["latency_regression"] = True
                    has_latency_regression = True
                    case_diff["details"].append(
                        f"Query '{q_name}' latency spike: {base_lat:.2f}ms -> {live_lat:.2f}ms (+{pct_increase:.0f}%, +{delta_ms:.2f}ms)"
                    )

            diff_cases.append(case_diff)

        # Overall Verdict
        has_drift = (has_schema_drift or has_status_drift)
        if not has_drift and not has_latency_regression:
            verdict = "IDENTICAL"
        elif not has_drift and has_latency_regression:
            verdict = "PERF_ALERT"
        else:
            verdict = "DRIFT_DETECTED"

        total_cases = len(diff_cases)
        clean_count = sum(1 for c in diff_cases if not c["schema_drift"] and c["status_match"] and not c["latency_regression"])
        drift_count = sum(1 for c in diff_cases if c["schema_drift"] or not c["status_match"])
        perf_count = sum(1 for c in diff_cases if c["latency_regression"])

        return {
            "verdict": verdict,
            "has_drift": has_drift,
            "has_schema_drift": has_schema_drift,
            "has_status_drift": has_status_drift,
            "has_latency_regression": has_latency_regression,
            "total_cases_evaluated": total_cases,
            "clean_cases_count": clean_count,
            "drifted_cases_count": drift_count,
            "perf_alert_cases_count": perf_count,
            "baseline_generated_at": snapshot.get("generated_at"),
            "cases": diff_cases
        }

    @classmethod
    def format_diff_terminal_report(cls, diff_res: Dict[str, Any]) -> str:
        """
        Renders a clean, formatted terminal diff report.
        """
        lines = [
            "\n=== 🔍 BENCHMARK HARNESS REGRESSION DIFF REPORT ===",
            f"Overall Verdict:        {diff_res['verdict']}",
            f"Clean Cases:            {diff_res['clean_cases_count']}/{diff_res['total_cases_evaluated']} matching baseline",
            f"Drifted Cases:          {diff_res['drifted_cases_count']} cases",
            f"Performance Alerts:     {diff_res['perf_alert_cases_count']} cases",
            f"Baseline Timestamp:     {diff_res.get('baseline_generated_at', 'N/A')}",
            "-" * 85
        ]

        for c in diff_res.get("cases", []):
            cid = c["case_id"]
            name = c["name"]
            
            if c.get("is_new_case"):
                badge = "[NEW]"
            elif c.get("schema_drift") or not c.get("status_match"):
                badge = "[DRIFT]"
            elif c.get("latency_regression"):
                badge = "[PERF ALERT]"
            else:
                badge = "[CLEAN]"

            lines.append(f"{badge:<13} {cid:<10} {name}")
            for d in c.get("details", []):
                lines.append(f"  └─ ⚠️  {d}")

        lines.append("-" * 85)
        if diff_res["verdict"] == "IDENTICAL":
            lines.append("✅ 100% IDENTICAL: Zero schema drift or status deviations detected against baseline.")
        elif diff_res["verdict"] == "PERF_ALERT":
            lines.append("⚠️  PERFORMANCE NOTICE: Schemas match 100%, but query latency regressions were flagged.")
        else:
            lines.append("🔴 SCHEMA / STATUS DRIFT DETECTED: Review details above or run with --snapshot to promote changes.")

        return "\n".join(lines)
