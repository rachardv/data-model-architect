from typing import Dict, Any

class DataModelDecisionEngine:
    """
    Cognitive decision engine implementing the '21 Questions' adaptive decision tree.
    Maps non-technical business usage parameters to optimal database architectures,
    including Transitive Closure Bridge tables and Multi-Currency Triads.
    """
    
    @staticmethod
    def classify_architecture(
        is_live_app: bool,
        is_high_frequency_stream: bool,
        needs_history: bool,
        has_retroactive_backdating: bool,
        has_multi_stage_milestones: bool,
        is_periodic_state_rollup: bool,
        has_high_churn_ml_scores: bool,
        has_recursive_hierarchy: bool = False,
        is_multi_currency: bool = False
    ) -> Dict[str, Any]:
        # 1. High-Frequency Streaming Telemetry / Market Data
        if is_high_frequency_stream:
            res = {
                "pattern": "TIMESCALEDB_HYPERTABLE",
                "storage": "Time-Series Hypertables",
                "schema_type": "Time-Series Partitioned",
                "temporal": "APPEND_ONLY_TIME_SERIES"
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 2. Recursive Hierarchy / Bill of Materials (BOM) / Org Charts
        if has_recursive_hierarchy:
            res = {
                "pattern": "RECURSIVE_HIERARCHY_CLOSURE",
                "storage": "Kimball Closure Bridge Table",
                "schema_type": "Transitive Closure Bridge + Conformed Dimensions",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE"
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 3. Pure OLTP Live Application
        if is_live_app and not needs_history:
            res = {
                "pattern": "OLTP_3NF_RELATIONAL",
                "storage": "Standard ANSI Relational",
                "schema_type": "3NF Normalized",
                "temporal": "SCD1_OVERWRITE"
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 4. Multi-Stage Lifecycle Tracking (Order -> Ship -> Deliver)
        if has_multi_stage_milestones:
            temporal_type = "BITEMPORAL" if has_retroactive_backdating else "SCD2_HISTORICAL"
            res = {
                "pattern": "ACCUMULATING_SNAPSHOT_FACT",
                "storage": "Kimball Star Schema",
                "schema_type": "Accumulating Snapshot Fact + Conformed Dimensions",
                "temporal": temporal_type
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 5. Periodic Snapshot (Monthly / Daily Balance Rollups)
        if is_periodic_state_rollup:
            if has_high_churn_ml_scores:
                res = {
                    "pattern": "PERIODIC_SNAPSHOT_MINIDIM",
                    "storage": "Kimball Star Schema",
                    "schema_type": "Periodic Snapshot Fact + Mini-Dimension Outrigger",
                    "temporal": "SCD2_CORE_PLUS_MINIDIM"
                }
            else:
                temporal_type = "BITEMPORAL" if has_retroactive_backdating else "SCD2_HISTORICAL"
                res = {
                    "pattern": "PERIODIC_SNAPSHOT_FACT",
                    "storage": "Kimball Star Schema",
                    "schema_type": "Periodic Snapshot Fact + SCD2 Dimension",
                    "temporal": temporal_type
                }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 6. SOX / Audit Grade Historical Reporting with Backdating
        if needs_history and has_retroactive_backdating:
            res = {
                "pattern": "BITEMPORAL_SCD2_ENGINE",
                "storage": "Bi-Temporal Relational",
                "schema_type": "Bi-Temporal Dimension + Transaction Fact",
                "temporal": "BITEMPORAL_VALID_AND_SYSTEM_TIME"
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # 7. Standard Historical Analytical Mart (SCD2)
        if needs_history:
            res = {
                "pattern": "KIMBALL_STAR_SCD2",
                "storage": "Kimball Star Schema",
                "schema_type": "Transaction Fact + SCD2 Dimension",
                "temporal": "SCD2_HISTORICAL"
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
        # Default: Standard Current-State Star Mart
        res = {
            "pattern": "KIMBALL_STAR_SCD1",
            "storage": "Kimball Star Schema",
            "schema_type": "Transaction Fact + SCD1 Dimension",
            "temporal": "SCD1_OVERWRITE"
        }
        if is_multi_currency:
            res["multi_currency_triad"] = True
        return res
