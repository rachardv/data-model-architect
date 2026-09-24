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
        is_multi_currency: bool = False,
        is_factless_event: bool = False,
        is_denormalized_obt: bool = False,
        is_nested_columnar: bool = False,
        has_multi_fact_bus_matrix: bool = False,
        has_scd6_hybrid: bool = False,
        has_semi_additive_balances: bool = False,
        has_multivalued_bridge: bool = False,
        has_junk_dimension: bool = False,
        has_outrigger_dimension: bool = False,
        is_data_vault: bool = False,
        is_graph_topology: bool = False,
        is_realtime_streaming_olap: bool = False,
        is_vector_feature_store: bool = False
    ) -> Dict[str, Any]:
        # 0. Data Vault 2.0 Raw Ingestion Layer (Hubs, Links, Satellites)
        if is_data_vault:
            res = {
                "pattern": "DATA_VAULT_2_RAW",
                "storage": "Data Vault 2.0 Raw Vault",
                "schema_type": "Hubs, Links, and Satellites with SHA-256 Hash Keys",
                "temporal": "APPEND_ONLY_INSERT_LOAD_DTS",
                "has_hash_keys": True,
                "has_multi_source_satellites": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0a. Graph OLAP Network Topology (Vertices & Directed Weighted Edges)
        if is_graph_topology:
            res = {
                "pattern": "GRAPH_PROPERTY_TOPOLOGY",
                "storage": "Graph Columnar Adjacency (Nodes & Edges)",
                "schema_type": "Property Graph Topology (Vertices and Directed Edges)",
                "temporal": "DIRECTED_TEMPORAL_EDGE",
                "has_recursive_traversal": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0b. Real-Time Columnar Streaming OLAP (ClickHouse / Pinot Wide Event Streams)
        if is_realtime_streaming_olap:
            res = {
                "pattern": "REALTIME_STREAMING_OLAP",
                "storage": "Real-Time Columnar Streaming Engine (ClickHouse/Pinot)",
                "schema_type": "Denormalized Streaming Event Table with Approximate HLL Sketches",
                "temporal": "STREAMING_INGESTION_TIME",
                "has_approx_sketches": True,
                "has_zero_join_streams": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0c. AI Vector Embeddings & Dual-Speed Feature Store (ASOF JOIN & Dense Vectors)
        if is_vector_feature_store:
            res = {
                "pattern": "VECTOR_FEATURE_STORE",
                "storage": "Dual-Speed Feature Store (Online KV + Offline Columnar)",
                "schema_type": "Time-Versioned Entity Features with Dense Vector Embeddings",
                "temporal": "POINT_IN_TIME_ASOF_JOIN",
                "has_vector_embeddings": True,
                "has_asof_joins": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0d. Factless Fact Table (Event Attendance / Coverage Matrix)
        if is_factless_event:
            return {
                "pattern": "FACTLESS_FACT_COVERAGE",
                "storage": "Kimball Star Schema",
                "schema_type": "Factless Event / Coverage Matrix",
                "temporal": "SCD1_OVERWRITE"
            }

        # 0b. Denormalized OBT Mart (Single Flat Table / Sub-Second Scan / Zero Join Latency)
        if is_denormalized_obt:
            return {
                "pattern": "DENORMALIZED_OBT_MART",
                "storage": "Columnar Flat Mart (OBT)",
                "schema_type": "Denormalized One Big Table",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE"
            }

        # 0c. Nested & Repeated Columnar Mart (ARRAY<STRUCT> / Parquet Native)
        if is_nested_columnar:
            return {
                "pattern": "NESTED_COLUMNAR_MART",
                "storage": "Nested Columnar (Parquet/BigQuery/DuckDB)",
                "schema_type": "Nested and Repeated Records (ARRAY<STRUCT>)",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE"
            }

        # 0d. Multi-Fact Enterprise Bus Matrix (Cross-Process Value Stream with Conformed Dimensions)
        if has_multi_fact_bus_matrix:
            return {
                "pattern": "MULTI_FACT_BUS_MATRIX",
                "storage": "Kimball Enterprise Bus Matrix",
                "schema_type": "Multi-Fact Dimensional Model with Conformed Dimensions",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE"
            }

        # 0e. SCD Type 6 Hybrid Dimension (Type 2 + Type 3 + Type 1 Dual Perspective)
        if has_scd6_hybrid:
            return {
                "pattern": "KIMBALL_STAR_SCD6",
                "storage": "Kimball Star Schema (Type 6 Hybrid)",
                "schema_type": "Transaction Fact + SCD Type 6 Hybrid Dimension",
                "temporal": "SCD6_HYBRID"
            }

        # 0f. Multi-Valued Dimension Bridge Table (M:N Relationships with Weighting Factors)
        if has_multivalued_bridge:
            res = {
                "pattern": "MULTIVALUED_BRIDGE_STAR",
                "storage": "Kimball Multi-Valued Bridge Schema",
                "schema_type": "Multi-Valued Dimension Bridge Table with Allocation Weighting",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE",
                "has_bridge_table": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0g. Consolidated Junk Dimension (Low-Cardinality Transaction Flags & Indicators)
        if has_junk_dimension:
            res = {
                "pattern": "JUNK_DIMENSION_CONSOLIDATION",
                "storage": "Kimball Star Schema (Junk Dimension)",
                "schema_type": "Transaction Fact with Consolidated Junk Dimension for Flags and Indicators",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE",
                "has_junk_dimension": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res

        # 0h. Dimension Outrigger Table (Secondary Dimension at Differing Grain)
        if has_outrigger_dimension:
            res = {
                "pattern": "KIMBALL_OUTRIGGER_STAR",
                "storage": "Kimball Star Schema (Outrigger Dimension)",
                "schema_type": "Dimension Outrigger Table at Secondary Grain",
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE",
                "has_outrigger_dimension": True
            }
            if is_multi_currency:
                res["multi_currency_triad"] = True
            return res
            
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
                "temporal": "SCD2_HISTORICAL" if needs_history else "SCD1_OVERWRITE",
                "has_closure_table": True
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
            
        # 5. Periodic Snapshot (Monthly / Daily Balance Rollups / Semi-Additive Balances)
        if is_periodic_state_rollup or has_semi_additive_balances:
            if has_high_churn_ml_scores:
                res = {
                    "pattern": "PERIODIC_SNAPSHOT_MINIDIM",
                    "storage": "Kimball Star Schema",
                    "schema_type": "Periodic Snapshot Fact + Mini-Dimension Outrigger",
                    "temporal": "SCD2_CORE_PLUS_MINIDIM",
                    "has_mini_dimension": True
                }
            else:
                temporal_type = "BITEMPORAL" if has_retroactive_backdating else "SCD2_HISTORICAL"
                schema_desc = "Periodic Snapshot Fact with Semi-Additive Balances and Aggregate Rollup Navigation" if has_semi_additive_balances else "Periodic Snapshot Fact + SCD2 Dimension"
                res = {
                    "pattern": "PERIODIC_SNAPSHOT_FACT",
                    "storage": "Kimball Star Schema (Periodic Snapshot)",
                    "schema_type": schema_desc,
                    "temporal": temporal_type,
                    "has_semi_additive_balances": has_semi_additive_balances,
                    "has_aggregate_rollups": has_semi_additive_balances
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
