"""
Unit and Integration Tests for Enterprise Validation Strategy & Pluggable Risk Architecture
Tests all 4 validation tiers across RSK-01 to RSK-09 and pluggable evaluator contracts.
"""

import pytest
import duckdb
from typing import Dict, Any

from src.validation_strategy import (
    ValidationTier,
    RiskSeverity,
    RiskResult,
    ValidationContext,
    BaseRiskEvaluator,
    RiskRegistry,
    ValidationStrategyEngine,
    register_risk
)
from src.chaos_engine import AdversarialChaosGenerator
from src.orchestration.captain import CaptainOrchestrator


@pytest.fixture
def clean_test_context() -> ValidationContext:
    schema = {
        "tables": [
            {
                "name": "dim_customers",
                "type": "DIMENSION",
                "grain": "one row per customer",
                "scd_type": 2,
                "primary_key": "customer_sk",
                "columns": [
                    {"name": "customer_sk", "type": "BIGINT", "primary_key": True},
                    {"name": "customer_id", "type": "VARCHAR"},
                    {"name": "email", "type": "VARCHAR"},
                    {"name": "valid_from", "type": "TIMESTAMP"},
                    {"name": "valid_to", "type": "TIMESTAMP"},
                    {"name": "is_current", "type": "BOOLEAN"}
                ]
            },
            {
                "name": "fct_orders",
                "type": "FACT",
                "grain": "one row per order line",
                "primary_key": "order_id",
                "columns": [
                    {"name": "order_id", "type": "VARCHAR", "primary_key": True},
                    {"name": "customer_sk", "type": "BIGINT", "foreign_key": "dim_customers.customer_sk"},
                    {"name": "order_timestamp", "type": "TIMESTAMP"},
                    {"name": "amount", "type": "DECIMAL(18,2)"}
                ]
            }
        ]
    }
    
    medallion = {
        "bronze": {"storage_format": "PARQUET", "schema_drift_enabled": True, "quarantine_enabled": True, "raw_preservation": True},
        "silver": {"quarantine_view": "silver_quarantine", "idempotent_merge": True, "dedup_strategy": "QUALIFY_ROW_NUMBER"},
        "gold": {"materialization": "TABLE", "additive_metrics_only": True}
    }
    
    dbt_proj = {
        "models": [
            {
                "name": "fct_orders",
                "sql": "SELECT o.order_id, o.customer_sk, c.email, o.amount FROM fct_orders o JOIN dim_customers c ON o.customer_sk = c.customer_sk"
            }
        ]
    }
    
    return ValidationContext(
        domain="ecommerce_validation",
        target_schema=schema,
        medallion_pipeline=medallion,
        dbt_project=dbt_proj
    )


class TestPluggableRiskRegistry:
    def test_registry_has_all_9_evaluators(self):
        registered_risks = RiskRegistry.list_risks()
        expected = {
            "RSK-01", "RSK-02", "RSK-03", "RSK-04",
            "RSK-05", "RSK-06", "RSK-07", "RSK-08", "RSK-09"
        }
        for rsk in expected:
            assert rsk in registered_risks

    def test_custom_plugin_registration(self):
        try:
            @register_risk("RSK-99-TEST")
            class CustomComplianceEvaluator(BaseRiskEvaluator):
                risk_id = "RSK-99-TEST"
                risk_name = "Custom Compliance Rule"
                tier = ValidationTier.TIER_1_STATIC_CONTRACT
                default_severity = RiskSeverity.MEDIUM

                def evaluate(self, ctx: ValidationContext) -> RiskResult:
                    return RiskResult(
                        risk_id=self.risk_id,
                        risk_name=self.risk_name,
                        tier=self.tier,
                        severity=self.default_severity,
                        status="PASS",
                        details="Custom compliance passed"
                    )

            evaluator_cls = RiskRegistry.get_evaluator("RSK-99-TEST")
            assert evaluator_cls is not None
            assert evaluator_cls.risk_id == "RSK-99-TEST"

            # Verify dynamic execution in engine
            ctx = ValidationContext(domain="test_custom", target_schema={"tables": []})
            res = ValidationStrategyEngine.evaluate(ctx)
            custom_results = [r for r in res["results"] if r["risk_id"] == "RSK-99-TEST"]
            assert len(custom_results) == 1
            assert custom_results[0]["status"] == "PASS"
        finally:
            RiskRegistry.unregister("RSK-99-TEST")


class TestAllTiersEvaluation:
    def test_clean_model_passes_all_tiers(self, clean_test_context):
        scorecard = ValidationStrategyEngine.evaluate(clean_test_context)
        
        assert scorecard["domain"] == "ecommerce_validation"
        assert scorecard["critical_halt"] is False
        assert scorecard["summary"]["FAIL"] == 0
        assert scorecard["summary"]["HALT"] == 0
        assert scorecard["score"] >= 95.0
        
        # Verify 4 tiers present
        tiers_present = {r["tier"] for r in scorecard["results"]}
        assert ValidationTier.TIER_1_STATIC_CONTRACT.value in tiers_present
        assert ValidationTier.TIER_2_RELATIONAL_INTEGRITY.value in tiers_present
        assert ValidationTier.TIER_3_PHYSICAL_RUNTIME.value in tiers_present
        assert ValidationTier.TIER_4_CHAOS_STRESS.value in tiers_present

    def test_rsk01_granularity_ambiguity_failure(self):
        # Schema with table missing grain and primary key
        bad_schema = {
            "tables": [
                {
                    "name": "ambiguous_table",
                    "columns": [{"name": "col_a", "type": "VARCHAR"}]
                }
            ]
        }
        ctx = ValidationContext(domain="bad_grain", target_schema=bad_schema)
        scorecard = ValidationStrategyEngine.evaluate(ctx)
        
        rsk01_results = [r for r in scorecard["results"] if r["risk_id"] == "RSK-01"]
        assert len(rsk01_results) > 0
        assert any(r["status"] in ("FAIL", "HALT") for r in rsk01_results)
        assert scorecard["critical_halt"] is True

    def test_rsk02_chasm_trap_fanout_detection(self):
        # Schema with chasm trap query joining disparate grains directly
        dbt_bad = {
            "models": [
                {
                    "name": "chasm_mart",
                    "sql": "SELECT o.id, p.id FROM fct_orders o JOIN fct_order_payments p ON o.order_id = p.order_id"
                }
            ]
        }
        schema = {
            "tables": [
                {"name": "fct_orders", "type": "FACT", "grain": "one row per order", "columns": [{"name": "id", "primary_key": True}]},
                {"name": "fct_order_payments", "type": "FACT", "grain": "one row per payment installment", "columns": [{"name": "id", "primary_key": True}]}
            ]
        }
        ctx = ValidationContext(domain="chasm_test", target_schema=schema, dbt_project=dbt_bad)
        scorecard = ValidationStrategyEngine.evaluate(ctx)
        
        rsk02_results = [r for r in scorecard["results"] if r["risk_id"] == "RSK-02"]
        assert len(rsk02_results) > 0
        assert any(r["status"] in ("FAIL", "HALT") for r in rsk02_results)
        assert scorecard["critical_halt"] is True

    def test_rsk05_cyclic_fk_graph_detection(self):
        # Tables that form a circular FK reference: A -> B -> C -> A
        cyclic_schema = {
            "tables": [
                {"name": "table_a", "primary_key": "id", "columns": [{"name": "id", "primary_key": True}, {"name": "b_id", "foreign_key": "table_b.id"}]},
                {"name": "table_b", "primary_key": "id", "columns": [{"name": "id", "primary_key": True}, {"name": "c_id", "foreign_key": "table_c.id"}]},
                {"name": "table_c", "primary_key": "id", "columns": [{"name": "id", "primary_key": True}, {"name": "a_id", "foreign_key": "table_a.id"}]}
            ]
        }
        ctx = ValidationContext(domain="cyclic_test", target_schema=cyclic_schema)
        scorecard = ValidationStrategyEngine.evaluate(ctx)
        
        rsk05_results = [r for r in scorecard["results"] if r["risk_id"] == "RSK-05"]
        assert len(rsk05_results) > 0
        assert any("cycle" in r["message"].lower() for r in rsk05_results)
        assert scorecard["critical_halt"] is True

    def test_rsk08_gdpr_pseudonymization_proof(self, clean_test_context):
        scorecard = ValidationStrategyEngine.evaluate(clean_test_context)
        rsk08_results = [r for r in scorecard["results"] if "RSK-08" in r["risk_id"]]
        assert len(rsk08_results) > 0
        assert any(r["status"] == "PASS" for r in rsk08_results)


class TestChaosEngineStandalone:
    def test_zipfian_skew_generator_determinism(self):
        keys1 = AdversarialChaosGenerator.generate_skewed_keys(n_rows=1000, n_keys=50, skew_alpha=1.5, seed=42)
        keys2 = AdversarialChaosGenerator.generate_skewed_keys(n_rows=1000, n_keys=50, skew_alpha=1.5, seed=42)
        assert keys1 == keys2

        from collections import Counter
        counts = Counter(keys1)
        top_10_count = sum(c for _, c in counts.most_common(10))
        assert top_10_count / 1000.0 >= 0.70  # Strong skew verified

    def test_memory_constrained_duckdb_execution(self):
        res = AdversarialChaosGenerator.run_memory_constrained_benchmark(
            memory_limit_mb=16,
            num_rows=1000,
            num_keys=20
        )
        assert res["oom_encountered"] is False
        assert res["rows_processed"] == 1000
        assert res["duration_ms"] > 0

    def test_gdpr_erasure_simulation(self):
        res = AdversarialChaosGenerator.simulate_gdpr_erasure(
            customer_count=50,
            orders_per_customer=3,
            customers_to_erase=1
        )
        assert res["erasure_compliant"] is True
        assert res["metric_conserved"] is True
        assert res["orphan_fks_detected"] == 0
        assert res["financial_discrepancy"] == 0.0


class TestEvaluatorExceptionPolicy:
    def test_critical_evaluator_exception_triggers_halt(self):
        try:
            @register_risk("RSK-TEST-CRITICAL-CRASH")
            class CrashEvaluator(BaseRiskEvaluator):
                risk_id = "RSK-TEST-CRITICAL-CRASH"
                risk_name = "Exploding Critical Check"
                tier = ValidationTier.TIER_1_STATIC_CONTRACT
                default_severity = RiskSeverity.CRITICAL

                def evaluate(self, ctx: ValidationContext) -> RiskResult:
                    raise RuntimeError("Catastrophic evaluation crash!")

            ctx = ValidationContext(domain="crash_test", target_schema={"tables": []})
            scorecard = ValidationStrategyEngine.evaluate(ctx)
            
            crash_results = [r for r in scorecard["results"] if r["risk_id"] == "RSK-TEST-CRITICAL-CRASH"]
            assert len(crash_results) == 1
            assert crash_results[0]["status"] == "HALT"
            assert scorecard["critical_halt"] is True
        finally:
            RiskRegistry.unregister("RSK-TEST-CRITICAL-CRASH")

    def test_low_evaluator_exception_produces_warning_not_halt(self):
        try:
            @register_risk("RSK-TEST-LOW-CRASH")
            class LowCrashEvaluator(BaseRiskEvaluator):
                risk_id = "RSK-TEST-LOW-CRASH"
                risk_name = "Exploding Low Check"
                tier = ValidationTier.TIER_4_CHAOS_STRESS
                default_severity = RiskSeverity.LOW

                def evaluate(self, ctx: ValidationContext) -> RiskResult:
                    raise ValueError("Minor parser glitch")

            clean_schema = {
                "tables": [
                    {
                        "name": "dim_test",
                        "type": "DIMENSION",
                        "grain": "one per test",
                        "primary_key": "id",
                        "columns": [{"name": "id", "primary_key": True}]
                    }
                ]
            }
            ctx = ValidationContext(domain="low_crash_test", target_schema=clean_schema)
            scorecard = ValidationStrategyEngine.evaluate(ctx)
            
            crash_results = [r for r in scorecard["results"] if r["risk_id"] == "RSK-TEST-LOW-CRASH"]
            assert len(crash_results) == 1
            assert crash_results[0]["status"] == "EVALUATOR_ERROR"
        finally:
            RiskRegistry.unregister("RSK-TEST-LOW-CRASH")


class TestCaptainOrchestratorValidationIntegration:
    def test_captain_executes_validation_strategy_in_workflow(self):
        orchestrator = CaptainOrchestrator()
        payload = {
            "domain": "test_captain_val",
            "branch": "NEW_MODEL",
            "narrative": "A customer purchases items online. Each transaction is recorded as an order with payment details.",
            "usage_params": {
                "is_live_app": False,
                "is_high_frequency_stream": False,
                "needs_history": True,
                "has_retroactive_backdating": False,
                "has_multi_stage_milestones": False,
                "is_periodic_state_rollup": False,
                "has_high_churn_ml_scores": False
            }
        }
        
        result = orchestrator.execute_workflow(payload)
        
        assert "validation_risk_scorecard" in result
        scorecard = result["validation_risk_scorecard"]
        assert "critical_halt" in scorecard
        assert "summary" in scorecard
        assert "score" in scorecard
        assert isinstance(scorecard["results"], list)
        assert len(scorecard["results"]) >= 9
        assert result["status"] == "CERTIFIED_PRODUCTION_READY"
