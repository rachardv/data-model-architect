from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class VerificationQuery(BaseModel):
    """
    Physical SQL verification assertion executed directly against DuckDB tables
    to confirm that the data modeler correctly synthesized schemas, grains, and invariants.
    """
    name: str = Field(..., description="Short name of the verification check")
    query: str = Field(..., description="Executable DuckDB SQL query")
    assertion_type: str = Field(
        ...,
        description="Type of assertion: scalar_eq, scalar_gt, scalar_gte, scalar_lt, scalar_lte, row_count_gt, row_count_eq, is_empty, zero_drift, not_null"
    )
    expected_value: Any = Field(..., description="Expected scalar value or row count")
    failure_message: str = Field(..., description="Diagnostic message if assertion fails")

class PredefinedBenchmarkCase(BaseModel):
    """
    Curated enterprise benchmark test case containing complete business narrative,
    intake answers to satisfy Gate 0, hazard classification, intentional trap flags,
    and post-modeling SQL verification queries.
    """
    case_id: str = Field(..., description="Unique case identifier, e.g. CASE-01")
    domain: str = Field(..., description="Business domain name")
    name: str = Field(..., description="Human-readable case title")
    description: str = Field(..., description="Brief description of what the test case evaluates")
    hazard_category: str = Field(
        ...,
        description="Hazard or trap type: CLEAN_BASELINE, CHASM_TRAP_FANOUT, CYCLIC_FK_GRAPH, CONTRADICTION_HALT, SCD2_HISTORICAL_AMNESIA, BRIDGE_CO_OWNERSHIP, GRAIN_MISMATCH"
    )
    is_intentional_trap: bool = Field(False, description="True if case is designed to test defense guardrails by provoking a halt")
    prompt: str = Field(..., description="Initial business narrative with complete information")
    business_answers: List[str] = Field(default_factory=list, description="Plain-English answers to satisfy Gate 0 intake vectors")
    usage_params: Optional[Dict[str, Any]] = Field(default=None, description="Explicit usage workload parameters")
    rules: Optional[List[Dict[str, Any]]] = Field(default=None, description="Business rules / invariants")
    baseline_vectors: Optional[Dict[str, Any]] = Field(default=None, description="Baseline vectors for conflict checks")
    architectural_choice: Optional[str] = Field(default=None, description="Resolution pattern for architectural conflicts")
    schema_spec: Optional[Dict[str, Any]] = Field(default=None, description="Optional explicit schema override for trap testing")
    expected_status: str = Field(
        "CERTIFIED_PRODUCTION_READY",
        description="Expected final Captain status: CERTIFIED_PRODUCTION_READY, CRITICAL_RISK_HALT, AWAITING_ARCHITECTURAL_CONFIRMATION, INTAKE_INCOMPLETE_BLOCKED"
    )
    verification_queries: List[VerificationQuery] = Field(
        default_factory=list,
        description="SQL queries that assert the modeler modeled the domain correctly in DuckDB"
    )

# Mutable runtime registry for dynamically or externally loaded cases
_REGISTERED_CASES: List[PredefinedBenchmarkCase] = []

def register_benchmark_case(case: PredefinedBenchmarkCase) -> None:
    """Registers a predefined benchmark case into the runtime catalog."""
    _REGISTERED_CASES.append(case)

def clear_registered_benchmark_cases() -> None:
    """Clears all dynamically registered benchmark cases."""
    _REGISTERED_CASES.clear()

def get_predefined_benchmark_catalog() -> List[PredefinedBenchmarkCase]:
    """
    Returns the predefined benchmark catalog.
    Defaults to empty until populated by the user via registration or external data source.
    """
    return list(_REGISTERED_CASES)
