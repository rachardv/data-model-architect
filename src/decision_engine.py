from typing import Dict, Any

class DataModelDecisionEngine:
    """
    Cognitive decision engine implementing the '21 Questions' adaptive decision tree.
    Maps non-technical business usage parameters to optimal database architectures.
    """
    
    @staticmethod
    def classify_architecture(
        is_live_app: bool,
        is_high_frequency_stream: bool,
        needs_history: bool,
        has_retroactive_backdating: bool,
        has_multi_stage_milestones: bool,
        is_periodic_state_rollup: bool,
        has_high_churn_ml_scores: bool
    ) -> Dict[str, Any]:
        # 1. High-Frequency Streaming Telemetry / Market Data
        if is_high_frequency_stream:
            return {
                "pattern": "TIMESCALEDB_HYPERTABLE",
                "storage": "Time-Series Hypertables",
                "schema_type": "Time-Series Partitioned",
                "temporal": "APPEND_ONLY_TIME_SERIES"
            }
            
        # 2. Pure OLTP Live Application
        if is_live_app and not needs_history:
            return {
                "pattern": "OLTP_3NF_RELATIONAL",
                "storage": "Standard ANSI Relational",
                "schema_type": "3NF Normalized",
                "temporal": "SCD1_OVERWRITE"
            }
            
        # 3. Multi-Stage Lifecycle Tracking (Order -> Ship -> Deliver)
        if has_multi_stage_milestones:
            temporal_type = "BITEMPORAL" if has_retroactive_backdating else "SCD2_HISTORICAL"
            return {
                "pattern": "ACCUMULATING_SNAPSHOT_FACT",
                "storage": "Kimball Star Schema",
                "schema_type": "Accumulating Snapshot Fact + Conformed Dimensions",
                "temporal": temporal_type
            }
            
        # 4. Periodic Snapshot (Monthly / Daily Balance Rollups)
        if is_periodic_state_rollup:
            if has_high_churn_ml_scores:
                return {
                    "pattern": "PERIODIC_SNAPSHOT_MINIDIM",
                    "storage": "Kimball Star Schema",
                    "schema_type": "Periodic Snapshot Fact + Mini-Dimension Outrigger",
                    "temporal": "SCD2_CORE_PLUS_MINIDIM"
                }
            temporal_type = "BITEMPORAL" if has_retroactive_backdating else "SCD2_HISTORICAL"
            return {
                "pattern": "PERIODIC_SNAPSHOT_FACT",
                "storage": "Kimball Star Schema",
                "schema_type": "Periodic Snapshot Fact + SCD2 Dimension",
                "temporal": temporal_type
            }
            
        # 5. SOX / Audit Grade Historical Reporting with Backdating
        if needs_history and has_retroactive_backdating:
            return {
                "pattern": "BITEMPORAL_SCD2_ENGINE",
                "storage": "Bi-Temporal Relational",
                "schema_type": "Bi-Temporal Dimension + Transaction Fact",
                "temporal": "BITEMPORAL_VALID_AND_SYSTEM_TIME"
            }
            
        # 6. Standard Historical Analytical Mart (SCD2)
        if needs_history:
            return {
                "pattern": "KIMBALL_STAR_SCD2",
                "storage": "Kimball Star Schema",
                "schema_type": "Transaction Fact + SCD2 Dimension",
                "temporal": "SCD2_HISTORICAL"
            }
            
        # Default: Standard Current-State Star Mart
        return {
            "pattern": "KIMBALL_STAR_SCD1",
            "storage": "Kimball Star Schema",
            "schema_type": "Transaction Fact + SCD1 Dimension",
            "temporal": "SCD1_OVERWRITE"
        }
