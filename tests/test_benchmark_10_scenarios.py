import pytest
from src.decision_engine import DataModelDecisionEngine

BENCHMARK_SCENARIOS = [
    {
        "id": "TPC-DS-01",
        "domain": "TPC-DS Store Returns",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "KIMBALL_STAR_SCD2"
    },
    {
        "id": "KIMBALL-CH03",
        "domain": "E-Commerce Order Fulfillment Lifecycle",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT"
    },
    {
        "id": "KIMBALL-CH09",
        "domain": "Retail Bank Account Daily Balances",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_FACT"
    },
    {
        "id": "QUANT-FLOW-01",
        "domain": "High-Frequency Options Sweep Ticks (5,000 msgs/sec)",
        "params": {
            "is_live_app": True,
            "is_high_frequency_stream": True,
            "needs_history": False,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE"
    },
    {
        "id": "SOX-HR-01",
        "domain": "Corporate HR Retroactive Pay Raises",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": True,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "BITEMPORAL_SCD2_ENGINE"
    },
    {
        "id": "OLTP-AUTH-01",
        "domain": "Mobile App User Signup & Authentication",
        "params": {
            "is_live_app": True,
            "is_high_frequency_stream": False,
            "needs_history": False,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "OLTP_3NF_RELATIONAL"
    },
    {
        "id": "HEALTHCARE-01",
        "domain": "Hospital Patient Stay Milestones",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT"
    },
    {
        "id": "INSURANCE-01",
        "domain": "P&C Insurance Claim Loss Adjustment Lifecycle",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": True,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "ACCUMULATING_SNAPSHOT_FACT"
    },
    {
        "id": "IOT-FLEET-01",
        "domain": "Connected Vehicle GPS Telemetry",
        "params": {
            "is_live_app": True,
            "is_high_frequency_stream": True,
            "needs_history": False,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": False,
            "has_high_churn_ml_scores": False
        },
        "expected_pattern": "TIMESCALEDB_HYPERTABLE"
    },
    {
        "id": "SAAS-CHURN-01",
        "domain": "SaaS Monthly Subscription MRR + ML Churn Score Outrigger",
        "params": {
            "is_live_app": False,
            "is_high_frequency_stream": False,
            "needs_history": True,
            "has_retroactive_backdating": False,
            "has_multi_stage_milestones": False,
            "is_periodic_state_rollup": True,
            "has_high_churn_ml_scores": True
        },
        "expected_pattern": "PERIODIC_SNAPSHOT_MINIDIM"
    }
]

@pytest.mark.parametrize("scenario", BENCHMARK_SCENARIOS, ids=[s["id"] for s in BENCHMARK_SCENARIOS])
def test_data_modeler_ground_truth_accuracy(scenario):
    decision = DataModelDecisionEngine.classify_architecture(**scenario["params"])
    assert decision["pattern"] == scenario["expected_pattern"]
