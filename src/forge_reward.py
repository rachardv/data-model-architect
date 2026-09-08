import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.logger import get_logger

logger = get_logger("forge_reward")

class StudioPolicyWeights(BaseModel):
    """
    Tunable architectural decision weights and heuristic policies consumed by the Studio Workflow.
    Adjusted iteratively by the Forge Workflow based on empirical reward signals.
    """
    version: int = Field(default=1, description="Policy weight iteration version")
    last_adjusted_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    atomic_grain_bias: float = Field(default=1.0, description="Bias towards atomic event-level grain vs summary rollup")
    bridge_mitigation_bias: float = Field(default=1.0, description="Preference for decoupling multi-valued co-ownership via bridge tables")
    scd2_outrigger_bias: float = Field(default=1.0, description="Preference for SCD2 outrigger isolation vs inline dimension widening")
    relational_join_depth_penalty: float = Field(default=1.0, description="Penalty against multi-hop snowflake join trees to minimize relational algebra")
    quarantine_strictness: float = Field(default=1.0, description="Sensitivity threshold for routing corrupt records to Silver quarantine")

class ForgeRewardSignals(BaseModel):
    """
    Decomposed reward vector computed by the Forge Workflow from physical benchmark outcomes.
    """
    metric_conservation_reward: float = Field(default=1.0, ge=0.0, le=1.0)
    temporal_causality_reward: float = Field(default=1.0, ge=0.0, le=1.0)
    referential_integrity_reward: float = Field(default=1.0, ge=0.0, le=1.0)
    relational_algebra_reward: float = Field(default=1.0, ge=0.0, le=1.0)
    trap_defense_reward: float = Field(default=1.0, ge=0.0, le=1.0)
    composite_reward: float = Field(default=1.0, ge=0.0, le=1.0)

class ForgeRewardEngine:
    """
    Evaluates physical benchmark execution results and computes composite reward signals.
    """

    @classmethod
    def compute_reward(cls, scorecard: Dict[str, Any]) -> ForgeRewardSignals:
        """
        Computes normalized scalar rewards [0.0 - 1.0] across physical dimensions.
        """
        # 1. Metric Conservation Reward (TPC-DI & Industry suites)
        r_metric = 1.0
        ind = scorecard.get("industry_standards_gate", {})
        if ind:
            if ind.get("tpcdi", {}).get("metric_drift", 0.0) > 0.0:
                r_metric = 0.5
            if ind.get("overall_status") != "PASS":
                r_metric = min(r_metric, 0.8)

        # 2. Temporal Causality (SCD2 Point-in-time)
        r_temporal = 1.0
        if ind and ind.get("tpcdi", {}).get("audits_passed", 0) < ind.get("tpcdi", {}).get("total_audits", 1):
            r_temporal = 0.6

        # 3. Referential & Grain Integrity
        r_integrity = 1.0
        if ind and ind.get("tpch", {}).get("status") != "PASS":
            r_integrity = 0.7

        # 4. Relational Algebra Minimization (Sub-100ms execution, zero Cartesian)
        r_algebra = 1.0
        total_time_ms = scorecard.get("execution_time_ms", 0.0)
        if total_time_ms > 5000.0:
            r_algebra = 0.7
        elif total_time_ms > 2000.0:
            r_algebra = 0.9

        # 5. Trap Defense Reward (Predefined Gate halts)
        r_trap = 1.0
        predefined = scorecard.get("predefined_benchmark_gate", {})
        if predefined and predefined.get("trap_defenses_tested", 0) > 0:
            traps_tested = predefined.get("trap_defenses_tested", 1)
            traps_passed = predefined.get("trap_defenses_passed", 0)
            r_trap = traps_passed / traps_tested

        # Composite weighted sum
        composite = round(
            (0.25 * r_metric) +
            (0.25 * r_temporal) +
            (0.20 * r_integrity) +
            (0.15 * r_algebra) +
            (0.15 * r_trap),
            4
        )

        return ForgeRewardSignals(
            metric_conservation_reward=r_metric,
            temporal_causality_reward=r_temporal,
            referential_integrity_reward=r_integrity,
            relational_algebra_reward=r_algebra,
            trap_defense_reward=r_trap,
            composite_reward=composite
        )

class ForgeWeightAdjuster:
    """
    Adjusts Studio policy weights based on Forge reward signals and persists the updated policy.
    """

    @classmethod
    def load_weights(cls, path: str = "config/studio_policy_weights.json") -> StudioPolicyWeights:
        """Loads current Studio policy weights or returns defaults."""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return StudioPolicyWeights(**data)
            except Exception as e:
                logger.warning(f"Failed to load weights from {path}: {e}. Using defaults.")
        return StudioPolicyWeights()

    @classmethod
    def adjust_and_save(
        cls,
        reward_signals: ForgeRewardSignals,
        learning_rate: float = 0.05,
        path: str = "config/studio_policy_weights.json"
    ) -> StudioPolicyWeights:
        """
        Applies gradient adjustments to Studio policy weights based on reward signals,
        then persists to disk.
        """
        weights = cls.load_weights(path)
        weights.version += 1
        weights.last_adjusted_utc = datetime.now(timezone.utc).isoformat()

        # If relational algebra latency is suboptimal, increase join depth penalty
        if reward_signals.relational_algebra_reward < 0.95:
            weights.relational_join_depth_penalty += round(learning_rate * 2.0, 3)
            weights.bridge_mitigation_bias += round(learning_rate, 3)
        else:
            weights.relational_join_depth_penalty = max(1.0, round(weights.relational_join_depth_penalty - (learning_rate * 0.5), 3))

        # If temporal causality reward dropped, boost SCD2 outrigger bias
        if reward_signals.temporal_causality_reward < 1.0:
            weights.scd2_outrigger_bias += round(learning_rate * 1.5, 3)

        # If referential integrity or quarantine dropped, boost quarantine strictness
        if reward_signals.referential_integrity_reward < 1.0:
            weights.quarantine_strictness += round(learning_rate * 1.5, 3)

        # Save to disk
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(weights.model_dump(), f, indent=2)

        logger.info(f"Forge adjusted Studio policy weights (v{weights.version}) saved to {path}")
        return weights
