from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ForgeIntakeSpec(BaseModel):
    """
    Decoupled Machine-Level Intake Specification for Forge Workflow.
    Unlike Studio Intake (which evaluates natural language narratives and conducts 21-Question interviews),
    Forge Intake receives optimization parameters, benchmark targets, and reward thresholds.
    """
    target_environment: str = Field(default="local_duckdb", description="Target execution runtime for certification")
    optimization_mode: str = Field(default="BALANCED", description="Optimization profile: BALANCED, MIN_RELATIONAL_ALGEBRA, MAX_REVENUE_INTEGRITY, LATENCY_FIRST")
    reward_threshold: float = Field(default=0.95, description="Minimum acceptable composite reward score [0.0 - 1.0]")
    suites_enabled: List[str] = Field(default_factory=lambda: ["predefined_gate", "industry_standards", "academic_semantics"])
    learning_rate: float = Field(default=0.05, description="Rate of policy weight adjustment per Forge certification run")
    weights_path: str = Field(default="config/studio_policy_weights.json", description="Target path for adjusted Studio weights")

class ForgeIntakeEngine:
    """
    Machine-Level Intake Engine for the Forge Workflow.
    Prepares certification specs without conversational business discovery.
    """

    @classmethod
    def process_forge_intake(cls, config_overrides: Optional[Dict[str, Any]] = None) -> ForgeIntakeSpec:
        """
        Parses and validates the Forge Intake specification.
        """
        overrides = config_overrides or {}
        return ForgeIntakeSpec(**overrides)
