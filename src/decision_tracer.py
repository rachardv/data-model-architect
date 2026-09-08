import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class VerificationQueryTrace(BaseModel):
    name: str
    query: str
    assertion_type: str
    expected_value: Any
    actual_value: Optional[Any] = None
    passed: bool
    latency_ms: float
    error: Optional[str] = None

class DecisionTrace(BaseModel):
    case_id: str
    domain: str
    name: str
    hazard_category: str
    is_intentional_trap: bool
    prompt: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    intake_decisions: Dict[str, Any] = Field(default_factory=dict)
    architecture_decisions: Dict[str, Any] = Field(default_factory=dict)
    schema_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    validation_decisions: Dict[str, Any] = Field(default_factory=dict)
    verification_queries_trace: List[VerificationQueryTrace] = Field(default_factory=list)
    final_status: str = "PENDING"
    expected_status: str = "CERTIFIED_PRODUCTION_READY"
    verdict: str = "PENDING"  # "PASS" or "FAIL"
    execution_time_ms: float = 0.0

class DecisionTracer:
    """
    Autonomous Modeler Decision Traceability Engine.
    Records every architectural, structural, and semantic decision made by the modeler,
    logs query execution latency and assertions, and cleanly overwrites previous deployment
    traces upon each execution run.
    """

    def __init__(
        self,
        case_id: str,
        domain: str,
        name: str,
        hazard_category: str,
        is_intentional_trap: bool,
        prompt: str,
        expected_status: str = "CERTIFIED_PRODUCTION_READY"
    ):
        self._start_time = time.perf_counter()
        self.trace = DecisionTrace(
            case_id=case_id,
            domain=domain,
            name=name,
            hazard_category=hazard_category,
            is_intentional_trap=is_intentional_trap,
            prompt=prompt,
            expected_status=expected_status
        )

    def record_intake(self, intake_result: Dict[str, Any]) -> None:
        """Audits Phase 0 Intake Squad & Vector analysis choices."""
        self.trace.intake_decisions = {
            "status": intake_result.get("status"),
            "completeness_score": intake_result.get("completeness_score"),
            "resolved_vectors": intake_result.get("resolved_vectors", {}),
            "missing_vectors": intake_result.get("missing_vectors", []),
            "parsed_semantics": intake_result.get("parsed_semantics", {})
        }

    def record_architecture(self, workflow_result: Dict[str, Any]) -> None:
        """Audits cognitive decision tree path and paradigm selection."""
        self.trace.architecture_decisions = {
            "architecture_pattern": workflow_result.get("architecture_pattern"),
            "inferred_usage_params": workflow_result.get("inferred_usage_params"),
            "resolution_applied": workflow_result.get("resolution_applied"),
            "disposition_matrix": workflow_result.get("disposition_matrix", [])
        }

    def record_schema(self, schema_spec: Dict[str, Any]) -> None:
        """Audits physical DDL entity choices, keys, and column typings."""
        tables_summary = []
        for tbl in schema_spec.get("tables", []):
            tables_summary.append({
                "table_name": tbl.get("name"),
                "type": tbl.get("type"),
                "primary_key": tbl.get("primary_key"),
                "column_count": len(tbl.get("columns", [])),
                "columns": [c.get("name") for c in tbl.get("columns", [])]
            })
        self.trace.schema_decisions = tables_summary

    def record_validation(self, validation_risk_scorecard: Dict[str, Any], benchmark_scorecard: Optional[Dict[str, Any]] = None) -> None:
        """Audits Reviewer Council 4-Tier findings and Physical Benchmark scores."""
        self.trace.validation_decisions = {
            "risk_scorecard_status": validation_risk_scorecard.get("overall_status") if validation_risk_scorecard else None,
            "critical_halt": validation_risk_scorecard.get("critical_halt", False) if validation_risk_scorecard else False,
            "tier_scores": validation_risk_scorecard.get("tier_scores", {}) if validation_risk_scorecard else {},
            "benchmark_overall_score": benchmark_scorecard.get("overall_score") if benchmark_scorecard else None,
            "benchmark_status": benchmark_scorecard.get("overall_status") if benchmark_scorecard else None
        }

    def record_query_verification(
        self,
        name: str,
        query: str,
        assertion_type: str,
        expected_value: Any,
        actual_value: Optional[Any],
        passed: bool,
        latency_ms: float,
        error: Optional[str] = None
    ) -> None:
        """Logs individual physical SQL verification assertion run against DuckDB."""
        self.trace.verification_queries_trace.append(
            VerificationQueryTrace(
                name=name,
                query=query,
                assertion_type=assertion_type,
                expected_value=expected_value,
                actual_value=actual_value,
                passed=passed,
                latency_ms=round(latency_ms, 2),
                error=error
            )
        )

    def finalize(self, final_status: str) -> None:
        """Finalizes trace verdict and computes execution duration."""
        self.trace.final_status = final_status
        self.trace.execution_time_ms = round((time.perf_counter() - self._start_time) * 1000, 2)
        
        # Check verdict
        status_match = (self.trace.final_status == self.trace.expected_status)
        all_queries_pass = all(q.passed for q in self.trace.verification_queries_trace)
        
        self.trace.verdict = "PASS" if (status_match and all_queries_pass) else "FAIL"

    def save(self, trace_dir: str = "docs/benchmarks/traces") -> Dict[str, str]:
        """
        Persists decision trace to disk with clean overwrite semantics.
        Creates <case_id>_trace.json and human-readable <case_id>_trace.md.
        """
        os.makedirs(trace_dir, exist_ok=True)
        base_name = self.trace.case_id.replace(" ", "_").upper()
        
        json_path = os.path.join(trace_dir, f"{base_name}_trace.json")
        md_path = os.path.join(trace_dir, f"{base_name}_trace.md")

        # 1. Overwrite JSON Trace
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.trace.model_dump(), f, indent=2)

        # 2. Overwrite Markdown Report
        md_content = self._generate_markdown_report()
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {"json_path": json_path, "md_path": md_path}

    def _generate_markdown_report(self) -> str:
        t = self.trace
        badge = "🟢 PASS" if t.verdict == "PASS" else "🔴 FAIL"
        trap_note = "⚠️ INTENTIONAL DEFENSE TRAP" if t.is_intentional_trap else "✅ VALID DOMAIN MODEL"
        
        lines = [
            f"# Decision Trace Report: {t.case_id} — {t.name}",
            f"",
            f"> **Verdict:** {badge} | **Type:** `{trap_note}` | **Runtime:** `{t.execution_time_ms}ms`",
            f"> **Timestamp (UTC):** `{t.timestamp_utc}`",
            f"",
            f"## 1. Case Metadata & Intent",
            f"- **Domain:** `{t.domain}`",
            f"- **Hazard Category:** `{t.hazard_category}`",
            f"- **Expected Status:** `{t.expected_status}`",
            f"- **Observed Final Status:** `{t.final_status}`",
            f"",
            f"### Business Prompt Narrative",
            f"```text",
            f"{t.prompt}",
            f"```",
            f"",
            f"## 2. Intake & Architectural Decisions",
            f"- **Completeness Score:** `{float(t.intake_decisions.get('completeness_score') or 0.0):.1f}%`",
            f"- **Selected Paradigm:** `{t.architecture_decisions.get('architecture_pattern', 'N/A')}`",
            f"- **Resolution Applied:** `{t.architecture_decisions.get('resolution_applied', 'NONE')}`",
            f"",
            f"## 3. Synthesized Schema Tables",
        ]

        if t.schema_decisions:
            lines.append("| Table Name | Type | Primary Key | Column Count |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for tbl in t.schema_decisions:
                lines.append(f"| `{tbl['table_name']}` | `{tbl['type']}` | `{tbl['primary_key']}` | {tbl['column_count']} |")
        else:
            lines.append("*No physical schema synthesized (execution halted by defensive guardrails).*")

        lines.extend([
            f"",
            f"## 4. Physical Verification Queries & Assertions",
        ])

        if t.verification_queries_trace:
            lines.append("| Query Name | Assertion | Expected | Actual | Latency | Status |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for q in t.verification_queries_trace:
                q_badge = "✅ PASS" if q.passed else "❌ FAIL"
                lines.append(f"| {q.name} | `{q.assertion_type}` | `{q.expected_value}` | `{q.actual_value}` | `{q.latency_ms}ms` | {q_badge} |")
                
            lines.append(f"")
            lines.append(f"### Query Details")
            for i, q in enumerate(t.verification_queries_trace, 1):
                lines.append(f"#### Query {i}: {q.name}")
                lines.append(f"```sql")
                lines.append(q.query)
                lines.append(f"```")
                if q.error:
                    lines.append(f"> [!CAUTION]")
                    lines.append(f"> **Query Error:** {q.error}")
        else:
            lines.append("*No verification queries specified for this case.*")

        lines.extend([
            f"",
            f"---",
            f"*Generated autonomously by Data Model Architect DecisionTracer. Cleanly overwritten upon redeployment.*"
        ])

        return "\n".join(lines)
