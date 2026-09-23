import re
from typing import Dict, Any, List, Optional
from src.schema_types import SchemaSpec, TableSpec, ColumnSpec, RelationshipSpec, AdditivityType
from src.bus_matrix import BusMatrixSynthesizer

class DynamicSchemaAuthor:
    """
    Domain-Driven Design (DDD) Autonomous Schema Synthesizer.
    Translates parsed business narrative semantics (actors, events, resources, hierarchies)
    and architecture decisions into formal Kimball-compliant Data Model Specifications.
    """

    @classmethod
    def synthesize_schema(
        cls,
        domain: str,
        parsed_semantics: Optional[Dict[str, Any]] = None,
        architecture_decision: Optional[Dict[str, Any]] = None,
        inferred_params: Optional[Dict[str, Any]] = None,
        user_request: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a complete schema specification dictionary conforming to SchemaSpec.
        """
        user_request = user_request or {}
        architecture_decision = architecture_decision or {}
        parsed_semantics = parsed_semantics or {}
        inferred_params = inferred_params or {}

        # 1. If explicit schema is provided by user, validate and return it directly
        if user_request.get("schema_spec") is not None:
            return user_request["schema_spec"]

        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        pattern = architecture_decision.get("pattern", "KIMBALL_STAR_SCD2")
        temporal_strategy = architecture_decision.get("temporal", "SCD2")
        is_multi_currency = architecture_decision.get("multi_currency_triad", False) or user_request.get("is_multi_currency", False)

        # 2a. Check for Data Vault 2.0 Raw Ingestion Layer
        if pattern == "DATA_VAULT_2_RAW" or inferred_params.get("is_data_vault"):
            return {
                "domain": clean_domain,
                "temporal_strategy": "APPEND_ONLY_INSERT_LOAD_DTS",
                "pattern": "DATA_VAULT_2_RAW",
                "tables": [
                    {
                        "name": "hub_customer",
                        "type": "HUB",
                        "description": "Data Vault 2.0 Customer Hub with SHA-256 Hash Key",
                        "primary_key": "customer_hk",
                        "columns": [
                            {"name": "customer_hk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "load_dts", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "rec_src", "type": "VARCHAR(64)", "nullable": False}
                        ]
                    },
                    {
                        "name": "hub_account",
                        "type": "HUB",
                        "description": "Data Vault 2.0 Account Hub with SHA-256 Hash Key",
                        "primary_key": "account_hk",
                        "columns": [
                            {"name": "account_hk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "account_number", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "load_dts", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "rec_src", "type": "VARCHAR(64)", "nullable": False}
                        ]
                    },
                    {
                        "name": "link_customer_account",
                        "type": "LINK",
                        "description": "Data Vault 2.0 Customer-Account Association Link",
                        "primary_key": "link_cust_account_hk",
                        "columns": [
                            {"name": "link_cust_account_hk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "customer_hk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": "hub_customer.customer_hk"},
                            {"name": "account_hk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": "hub_account.account_hk"},
                            {"name": "load_dts", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "rec_src", "type": "VARCHAR(64)", "nullable": False}
                        ]
                    },
                    {
                        "name": "sat_crm_customer",
                        "type": "SATELLITE",
                        "description": "Salesforce CRM Customer Satellite with Hash Diff Change Detection",
                        "primary_key": "customer_hk, load_dts",
                        "columns": [
                            {"name": "customer_hk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": "hub_customer.customer_hk"},
                            {"name": "load_dts", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "hash_diff", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "customer_name", "type": "VARCHAR(255)", "nullable": False},
                            {"name": "crm_tier", "type": "VARCHAR(32)", "nullable": False},
                            {"name": "email", "type": "VARCHAR(255)", "nullable": False},
                            {"name": "rec_src", "type": "VARCHAR(64)", "nullable": False}
                        ]
                    },
                    {
                        "name": "sat_billing_customer",
                        "type": "SATELLITE",
                        "description": "Stripe/SAP Billing Customer Satellite with Hash Diff",
                        "primary_key": "customer_hk, load_dts",
                        "columns": [
                            {"name": "customer_hk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": "hub_customer.customer_hk"},
                            {"name": "load_dts", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "hash_diff", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "credit_limit_usd", "type": "DECIMAL(14,2)", "nullable": False},
                            {"name": "billing_status", "type": "VARCHAR(32)", "nullable": False},
                            {"name": "rec_src", "type": "VARCHAR(64)", "nullable": False}
                        ]
                    }
                ]
            }

        # 2b. Check for Graph OLAP Network Topology (Vertices & Directed Weighted Edges)
        if pattern == "GRAPH_PROPERTY_TOPOLOGY" or inferred_params.get("is_graph_topology"):
            return {
                "domain": clean_domain,
                "temporal_strategy": "DIRECTED_TEMPORAL_EDGE",
                "pattern": "GRAPH_PROPERTY_TOPOLOGY",
                "tables": [
                    {
                        "name": f"graph_{clean_domain}_account_nodes",
                        "type": "VERTEX",
                        "description": "Graph OLAP Account Vertices (Nodes) with Risk Attributes",
                        "primary_key": "account_id",
                        "columns": [
                            {"name": "account_id", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "account_label", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "jurisdiction", "type": "VARCHAR(32)", "nullable": False},
                            {"name": "risk_score", "type": "DECIMAL(5,4)", "nullable": False}
                        ]
                    },
                    {
                        "name": f"graph_{clean_domain}_transfer_edges",
                        "type": "EDGE",
                        "description": "Graph OLAP Directed Weighted Edges with Recursive Traversal Support",
                        "primary_key": "edge_id",
                        "columns": [
                            {"name": "edge_id", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "source_account_id", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"graph_{clean_domain}_account_nodes.account_id"},
                            {"name": "target_account_id", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"graph_{clean_domain}_account_nodes.account_id"},
                            {"name": "amount_usd", "type": "DECIMAL(14,2)", "nullable": False},
                            {"name": "transfer_timestamp", "type": "TIMESTAMPTZ", "nullable": False}
                        ]
                    }
                ]
            }

        # 2c. Check for Real-Time Columnar Streaming OLAP (ClickHouse / Pinot Wide Event Streams)
        if pattern == "REALTIME_STREAMING_OLAP" or inferred_params.get("is_realtime_streaming_olap"):
            return {
                "domain": clean_domain,
                "temporal_strategy": "STREAMING_INGESTION_TIME",
                "pattern": "REALTIME_STREAMING_OLAP",
                "tables": [
                    {
                        "name": f"stream_{clean_domain}_clicks",
                        "type": "STREAMING_FACT",
                        "description": "Wide Denormalized Streaming Event Table for Sub-Second Columnar Aggregations",
                        "primary_key": "event_id",
                        "partition_by": "event_timestamp",
                        "columns": [
                            {"name": "event_id", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "event_timestamp", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "campaign_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "ad_placement", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "visitor_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "device_category", "type": "VARCHAR(32)", "nullable": False},
                            {"name": "geo_country", "type": "VARCHAR(16)", "nullable": False},
                            {"name": "bid_cost_usd", "type": "DECIMAL(10,4)", "nullable": False},
                            {"name": "is_converted", "type": "BOOLEAN", "nullable": False},
                            {"name": "revenue_usd", "type": "DECIMAL(14,2)", "nullable": False}
                        ]
                    }
                ]
            }

        # 2d. Check for AI Vector Embeddings & Dual-Speed Feature Store (ASOF JOIN & Dense Vectors)
        if pattern == "VECTOR_FEATURE_STORE" or inferred_params.get("is_vector_feature_store"):
            return {
                "domain": clean_domain,
                "temporal_strategy": "POINT_IN_TIME_ASOF_JOIN",
                "pattern": "VECTOR_FEATURE_STORE",
                "tables": [
                    {
                        "name": f"entity_{clean_domain}_customer_features",
                        "type": "FEATURE_STORE",
                        "description": "Offline Time-Versioned Customer Feature Store with Dense Affinity Vector Embeddings",
                        "primary_key": "customer_id, feature_timestamp",
                        "columns": [
                            {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "feature_timestamp", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "risk_velocity_30m", "type": "DOUBLE", "nullable": False},
                            {"name": "avg_order_value_30d", "type": "DECIMAL(14,2)", "nullable": False},
                            {"name": "affinity_embedding", "type": "FLOAT[4]", "nullable": False}
                        ]
                    },
                    {
                        "name": f"event_{clean_domain}_checkout_observations",
                        "type": "OBSERVATION_EVENT",
                        "description": "Ground Truth Observation Events for Point-in-Time ASOF Training Set Construction",
                        "primary_key": "observation_id",
                        "columns": [
                            {"name": "observation_id", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "observation_timestamp", "type": "TIMESTAMPTZ", "nullable": False},
                            {"name": "actual_fraud_label", "type": "BOOLEAN", "nullable": False},
                            {"name": "current_query_embedding", "type": "FLOAT[4]", "nullable": False}
                        ]
                    }
                ]
            }

        # 2e. Check for Factless Fact Table (Event Attendance / Coverage Matrix)
        if pattern == "FACTLESS_FACT_COVERAGE" or user_request.get("is_factless_event"):
            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD1",
                "pattern": "FACTLESS_FACT_COVERAGE",
                "tables": [
                    {
                        "name": f"dim_{clean_domain}_attendee",
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "columns": [
                            {"name": "attendee_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "attendee_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "attendee_name", "type": "VARCHAR(255)", "nullable": False}
                        ],
                        "primary_key": "attendee_sk"
                    },
                    {
                        "name": f"dim_{clean_domain}_event",
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "columns": [
                            {"name": "event_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                            {"name": "event_id", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "event_title", "type": "VARCHAR(255)", "nullable": False}
                        ],
                        "primary_key": "event_sk"
                    },
                    {
                        "name": f"fact_{clean_domain}_attendance_coverage",
                        "type": "FACTLESS_FACT",
                        "is_factless": True,
                        "composite_grain": ["attendee_sk", "event_sk", "date_sk"],
                        "description": "Factless fact tracking event attendance coverage with zero numeric measures",
                        "columns": [
                            {"name": "attendee_sk", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "event_sk", "type": "VARCHAR(64)", "nullable": False},
                            {"name": "date_sk", "type": "INT", "nullable": False}
                        ],
                        "primary_key": "attendee_sk, event_sk, date_sk"
                    }
                ]
            }

        # 3. Domain Entity Extraction
        domain_roles = parsed_semantics.get("domain_roles", {})
        raw_actor = domain_roles.get("primary_actor")
        raw_event = domain_roles.get("primary_event")
        raw_location = domain_roles.get("resource_location")

        # Standardize actor and event
        actor = "customer"
        if raw_actor and raw_actor.lower() not in ["user", "applicant", "actor"]:
            actor = re.sub(r"[^a-z0-9_]", "", raw_actor.lower())

        event = "orders"
        if raw_event and raw_event.lower() not in ["transaction", "event"]:
            event = re.sub(r"[^a-z0-9_]", "", raw_event.lower())
            if not event.endswith("s"):
                event += "s"

        # 3b. Check for Denormalized One Big Table (OBT) Mart
        if pattern == "DENORMALIZED_OBT_MART" or inferred_params.get("is_denormalized_obt"):
            obt_event = "subscriptions" if ("saas" in clean_domain or "sub" in clean_domain or "sub" in event) else event
            obt_table_name = f"obt_{clean_domain}_{obt_event}"
            sing_event = obt_event[:-1] if obt_event.endswith("s") else obt_event
            pk_col = f"{sing_event}_id"
            metric_col = "mrr_amount_usd" if ("saas" in clean_domain or "sub" in clean_domain) else "total_amount_usd"

            obt_columns = [
                {"name": pk_col, "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": f"{actor}_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": f"{actor}_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "email", "type": "VARCHAR(255)", "nullable": True, "is_inferred": False},
                {"name": "plan_tier", "type": "VARCHAR(64)", "nullable": False, "default": "'PRO'"} if "saas" in clean_domain else {"name": "product_category", "type": "VARCHAR(64)", "nullable": True},
                {"name": metric_col, "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
                {"name": "contract_duration_months" if "saas" in clean_domain else "order_status", "type": "INT" if "saas" in clean_domain else "VARCHAR(32)", "nullable": False}
            ]
            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD1",
                "pattern": "DENORMALIZED_OBT_MART",
                "tables": [
                    {
                        "name": obt_table_name,
                        "type": "FACT",
                        "description": "Denormalized One Big Table (OBT) analytical mart with zero join latency",
                        "primary_key": pk_col,
                        "columns": obt_columns
                    }
                ]
            }

        # 3c. Check for Nested Columnar Mart (ARRAY<STRUCT>)
        if pattern == "NESTED_COLUMNAR_MART" or inferred_params.get("is_nested_columnar"):
            mart_table_name = f"mart_{clean_domain}_{event}"
            sing_event = event[:-1] if event.endswith("s") else event
            pk_col = f"{sing_event}_id"
            actor_sk = f"{actor}_sk"
            dim_table_name = f"dim_{clean_domain}_{actor}_core" if actor == "customer" else f"dim_{clean_domain}_{actor}"

            mart_columns = [
                {"name": pk_col, "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": f"{actor}_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "total_amount_usd", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
                {"name": "order_status", "type": "VARCHAR(32)", "nullable": False, "default": "'COMPLETED'"},
                {"name": "items", "type": "STRUCT(item_id VARCHAR, product_name VARCHAR, quantity INT, unit_price DECIMAL(10,2))[]", "nullable": False}
            ]
            dim_columns = [
                {"name": actor_sk, "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": f"{actor}_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": f"{actor}_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 UTC'"},
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"}
            ]
            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD2",
                "pattern": "NESTED_COLUMNAR_MART",
                "tables": [
                    {
                        "name": dim_table_name,
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "primary_key": actor_sk,
                        "cluster_by": [actor_sk],
                        "columns": dim_columns
                    },
                    {
                        "name": mart_table_name,
                        "type": "FACT",
                        "description": "Nested and repeated columnar mart eliminating join fan-out traps",
                        "primary_key": pk_col,
                        "partition_by": "order_date_key",
                        "cluster_by": [f"{actor}_id"],
                        "columns": mart_columns
                    }
                ]
            }

        # 3d. Check for Multi-Fact Enterprise Bus Matrix
        if pattern == "MULTI_FACT_BUS_MATRIX" or inferred_params.get("has_multi_fact_bus_matrix") or user_request.get("has_multi_fact_bus_matrix"):
            domain_roles = parsed_semantics.get("domain_roles", {})
            value_stream_events = domain_roles.get("value_stream_events", ["orders", "shipments", "payments"])
            raw_actor = domain_roles.get("primary_actor")
            actor = "customer"
            if raw_actor and raw_actor.lower() not in ["user", "applicant", "actor"]:
                actor = re.sub(r"[^a-z0-9_]", "", raw_actor.lower())

            bus_matrix = BusMatrixSynthesizer.synthesize_bus_matrix(
                domain=clean_domain,
                actor=actor,
                events=value_stream_events
            )

            actor_sk = f"{actor}_sk"
            dim_actor_name = f"dim_{clean_domain}_{actor}_core" if actor == "customer" else f"dim_{clean_domain}_{actor}"

            dim_customer_cols = [
                {"name": actor_sk, "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": f"{actor}_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": f"{actor}_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "tier", "type": "VARCHAR(32)", "nullable": False, "default": "'STANDARD'"},
                {"name": "region", "type": "VARCHAR(64)", "nullable": True},
                {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 UTC'"},
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"}
            ]

            dim_product_cols = [
                {"name": "product_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "product_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "product_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "category", "type": "VARCHAR(64)", "nullable": True},
                {"name": "unit_price", "type": "DECIMAL(10,2)", "nullable": False, "default": "0.0"}
            ]

            dim_date_cols = [
                {"name": "date_sk", "type": "INT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "calendar_date", "type": "DATE", "nullable": False, "is_inferred": False},
                {"name": "calendar_year", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "calendar_month", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "calendar_quarter", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "day_of_week", "type": "VARCHAR(16)", "nullable": False, "is_inferred": False}
            ]

            bus_tables = [
                {
                    "name": dim_actor_name,
                    "type": "DIMENSION",
                    "is_conformed": True,
                    "primary_key": actor_sk,
                    "cluster_by": [actor_sk],
                    "columns": dim_customer_cols
                },
                {
                    "name": f"dim_{clean_domain}_product",
                    "type": "DIMENSION",
                    "is_conformed": True,
                    "primary_key": "product_sk",
                    "cluster_by": ["product_sk"],
                    "columns": dim_product_cols
                },
                {
                    "name": "dim_date",
                    "type": "DIMENSION",
                    "is_conformed": True,
                    "primary_key": "date_sk",
                    "cluster_by": ["date_sk"],
                    "columns": dim_date_cols
                }
            ]

            for f in bus_matrix.facts:
                sing_ev = f.name.replace(f"fact_{clean_domain}_", "").rstrip("s")
                pk_name = f"{sing_ev}_id"
                cols = [
                    {"name": pk_name, "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                    {"name": actor_sk, "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_actor_name}.{actor_sk}", "is_inferred": False}
                ]
                if "product_sk" in f.dimension_keys:
                    cols.append({"name": "product_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"dim_{clean_domain}_product.product_sk", "is_inferred": False})
                
                date_role = next((k for k in f.dimension_keys if "date" in k), "date_sk")
                cols.append({"name": date_role, "type": "INT", "nullable": False, "foreign_key": f"dim_date.date_sk", "is_inferred": False})

                if "ship" in f.name:
                    cols.append({"name": "carrier_name", "type": "VARCHAR(64)", "nullable": False, "default": "'FEDEX_EXPRESS'", "is_inferred": False})
                elif "pay" in f.name:
                    cols.append({"name": "payment_gateway", "type": "VARCHAR(64)", "nullable": False, "default": "'STRIPE'", "is_inferred": False})
                    cols.append({"name": "payment_status", "type": "VARCHAR(32)", "nullable": False, "default": "'SETTLED'", "is_inferred": False})

                for m in f.metric_columns:
                    m_type = "INT" if "quantity" in m else "DECIMAL(14,2)"
                    cols.append({"name": m, "type": m_type, "nullable": False, "is_inferred": False})

                fact_clusters = [k for k in [actor_sk, "product_sk"] if k in f.dimension_keys]
                bus_tables.append({
                    "name": f.name,
                    "type": "FACT",
                    "description": f"Conformed Enterprise Bus Matrix Fact: {f.grain}",
                    "primary_key": pk_name,
                    "partition_by": date_role,
                    "cluster_by": fact_clusters,
                    "columns": cols
                })

            drill_across_sql = bus_matrix.generate_drill_across_sql()

            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD2",
                "pattern": "MULTI_FACT_BUS_MATRIX",
                "bus_matrix": bus_matrix.model_dump(),
                "drill_across_sql": drill_across_sql,
                "tables": bus_tables
            }

        # 3e. Check for SCD Type 6 Hybrid Dimension (Type 2 + Type 3 + Type 1 Dual Perspective)
        if pattern == "KIMBALL_STAR_SCD6" or temporal_strategy in ["SCD6", "SCD6_HYBRID"] or inferred_params.get("has_scd6_hybrid") or user_request.get("has_scd6_hybrid"):
            dim_entity = "policy" if ("policy" in clean_domain or "insurance" in clean_domain) else actor
            if clean_domain.endswith(f"_{dim_entity}") or clean_domain == dim_entity:
                dim_table_name = f"dim_{clean_domain}_scd6"
            elif "scd6" in dim_entity:
                dim_table_name = f"dim_{clean_domain}_{dim_entity}"
            else:
                dim_table_name = f"dim_{clean_domain}_{dim_entity}_scd6"

            fact_event = "claims" if ("claim" in clean_domain or "insurance" in clean_domain or "claim" in event) else event
            fact_table_name = f"fact_{clean_domain}_{fact_event}"
            
            entity_sk = f"{dim_entity}_sk"
            entity_id = f"{dim_entity}_id"
            sing_event = fact_event[:-1] if fact_event.endswith("s") else fact_event
            event_id = f"{sing_event}_id"
            date_key_col = f"{sing_event}_date_key"

            dim_columns = [
                {"name": entity_sk, "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": entity_id, "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "policyholder_name" if dim_entity == "policy" else f"{dim_entity}_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "historical_risk_tier", "type": "VARCHAR(32)", "nullable": False, "default": "'STANDARD'"},
                {"name": "current_risk_tier", "type": "VARCHAR(32)", "nullable": False, "default": "'STANDARD'"},
                {"name": "historical_agent_region", "type": "VARCHAR(64)", "nullable": True},
                {"name": "current_agent_region", "type": "VARCHAR(64)", "nullable": True},
                {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 UTC'"},
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"},
                {"name": "version_number", "type": "INT", "nullable": False, "is_inferred": False, "default": "1"},
                {"name": "is_inferred", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "FALSE"}
            ]

            fact_columns = [
                {"name": event_id, "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": entity_sk, "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_table_name}.{entity_sk}", "is_inferred": False},
                {"name": date_key_col, "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "claim_amount" if "claim" in fact_event else "total_amount_usd", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
                {"name": "claim_status" if "claim" in fact_event else "status", "type": "VARCHAR(32)", "nullable": False, "default": "'OPEN'"}
            ]

            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD6_HYBRID",
                "pattern": "KIMBALL_STAR_SCD6",
                "tables": [
                    {
                        "name": dim_table_name,
                        "type": "DIMENSION",
                        "scd_type": 6,
                        "temporal_bounds": {"valid_from": "scd_valid_from", "valid_to": "scd_valid_to"},
                        "supports_ghost_records": True,
                        "is_conformed": True,
                        "primary_key": entity_sk,
                        "cluster_by": [entity_sk],
                        "columns": dim_columns
                    },
                    {
                        "name": fact_table_name,
                        "type": "FACT",
                        "primary_key": event_id,
                        "partition_by": date_key_col,
                        "cluster_by": [entity_sk],
                        "columns": fact_columns
                    }
                ]
            }

        # 3f. Check for Periodic Snapshot Balances & Aggregate Navigation Mart
        if pattern == "PERIODIC_SNAPSHOT_BALANCES" or inferred_params.get("has_semi_additive_balances") or user_request.get("has_semi_additive_balances"):
            dim_customer_name = f"dim_{clean_domain}_customer_core"
            dim_account_name = f"dim_{clean_domain}_account_core"
            dim_branch_name = f"dim_{clean_domain}_branch_core"
            dim_date_name = "dim_date"

            fact_snapshot_name = f"fact_daily_{clean_domain}_account_balances" if "banking" not in clean_domain else "fact_daily_account_balances"
            fact_event_name = f"fact_{clean_domain}_security_events" if "banking" not in clean_domain else "fact_customer_security_events"
            agg_rollup_name = f"agg_monthly_branch_{clean_domain}_balances" if "banking" not in clean_domain else "agg_monthly_branch_balances"

            dim_customer_cols = [
                {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "customer_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "customer_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "customer_tier", "type": "VARCHAR(32)", "nullable": False, "default": "'PREMIER'"},
                {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 UTC'"},
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"},
                {"name": "is_inferred", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "FALSE"}
            ]

            dim_account_cols = [
                {"name": "account_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "account_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "account_number", "type": "VARCHAR(32)", "nullable": False, "is_inferred": False},
                {"name": "account_type", "type": "VARCHAR(32)", "nullable": False, "default": "'CHECKING'"},
                {"name": "account_status", "type": "VARCHAR(32)", "nullable": False, "default": "'ACTIVE'"},
                {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_customer_name}.customer_sk", "is_inferred": False}
            ]

            dim_branch_cols = [
                {"name": "branch_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "branch_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "branch_name", "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
                {"name": "branch_city", "type": "VARCHAR(64)", "nullable": False},
                {"name": "branch_state", "type": "VARCHAR(32)", "nullable": False},
                {"name": "region", "type": "VARCHAR(64)", "nullable": False, "default": "'NORTH_AMERICA'"}
            ]

            dim_date_cols = [
                {"name": "date_sk", "type": "INT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "calendar_date", "type": "DATE", "nullable": False, "is_inferred": False},
                {"name": "calendar_year", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "calendar_month", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "calendar_quarter", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "day_of_week", "type": "VARCHAR(16)", "nullable": False, "is_inferred": False}
            ]

            fact_snapshot_cols = [
                {"name": "snapshot_id", "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "account_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_account_name}.account_sk", "is_inferred": False},
                {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_customer_name}.customer_sk", "is_inferred": False},
                {"name": "branch_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_branch_name}.branch_sk", "is_inferred": False},
                {"name": "snapshot_date_key", "type": "INT", "nullable": False, "foreign_key": f"{dim_date_name}.date_sk", "is_inferred": False},
                {"name": "ending_balance", "type": "DECIMAL(18,2)", "nullable": False, "additivity": "SEMI_ADDITIVE_TEMPORAL", "is_inferred": False},
                {"name": "available_balance", "type": "DECIMAL(18,2)", "nullable": False, "additivity": "SEMI_ADDITIVE_TEMPORAL", "is_inferred": False},
                {"name": "interest_rate_pct", "type": "DECIMAL(5,4)", "nullable": False, "additivity": "NON_ADDITIVE_RATIO", "formula": "weighted_interest / ending_balance", "is_inferred": False}
            ]

            fact_event_cols = [
                {"name": "event_sk", "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "customer_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_customer_name}.customer_sk", "is_inferred": False},
                {"name": "event_type", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "device_id", "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
                {"name": "event_date_key", "type": "INT", "nullable": False, "foreign_key": f"{dim_date_name}.date_sk", "is_inferred": False},
                {"name": "event_timestamp", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False}
            ]

            agg_rollup_cols = [
                {"name": "rollup_id", "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
                {"name": "branch_sk", "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_branch_name}.branch_sk", "is_inferred": False},
                {"name": "calendar_year", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "calendar_month", "type": "INT", "nullable": False, "is_inferred": False},
                {"name": "month_end_date_key", "type": "INT", "nullable": False, "foreign_key": f"{dim_date_name}.date_sk", "is_inferred": False},
                {"name": "total_closing_balance", "type": "DECIMAL(18,2)", "nullable": False, "additivity": "FULLY_ADDITIVE", "is_inferred": False},
                {"name": "total_accounts_count", "type": "INT", "nullable": False, "additivity": "FULLY_ADDITIVE", "is_inferred": False}
            ]

            return {
                "domain": clean_domain,
                "temporal_strategy": "SCD2",
                "pattern": "PERIODIC_SNAPSHOT_BALANCES",
                "tables": [
                    {
                        "name": dim_customer_name,
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "primary_key": "customer_sk",
                        "cluster_by": ["customer_sk"],
                        "columns": dim_customer_cols
                    },
                    {
                        "name": dim_account_name,
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "primary_key": "account_sk",
                        "cluster_by": ["account_sk"],
                        "columns": dim_account_cols
                    },
                    {
                        "name": dim_branch_name,
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "primary_key": "branch_sk",
                        "cluster_by": ["branch_sk"],
                        "columns": dim_branch_cols
                    },
                    {
                        "name": dim_date_name,
                        "type": "DIMENSION",
                        "is_conformed": True,
                        "primary_key": "date_sk",
                        "cluster_by": ["date_sk"],
                        "columns": dim_date_cols
                    },
                    {
                        "name": fact_snapshot_name,
                        "type": "PERIODIC_SNAPSHOT",
                        "description": "Daily account balance snapshot with semi-additive ending balances",
                        "primary_key": "snapshot_id",
                        "partition_by": "snapshot_date_key",
                        "cluster_by": ["account_sk", "branch_sk"],
                        "columns": fact_snapshot_cols
                    },
                    {
                        "name": fact_event_name,
                        "type": "FACTLESS_FACT",
                        "is_factless": True,
                        "composite_grain": ["customer_sk", "event_type", "device_id", "event_date_key"],
                        "description": "Factless security audit event log with zero numeric measures",
                        "primary_key": "event_sk",
                        "partition_by": "event_date_key",
                        "cluster_by": ["customer_sk"],
                        "columns": fact_event_cols
                    },
                    {
                        "name": agg_rollup_name,
                        "type": "AGGREGATE_ROLLUP",
                        "base_fact_table": fact_snapshot_name,
                        "rollup_grain": ["branch_sk", "calendar_year", "calendar_month"],
                        "description": "Pre-aggregated monthly branch closing balance summary for aggregate navigation",
                        "primary_key": "rollup_id",
                        "columns": agg_rollup_cols
                    }
                ]
            }

        # Table naming conventions
        # Preserve standard dim_{domain}_customer_core and fact_{domain}_orders for ecommerce / retail
        dim_table_name = f"dim_{clean_domain}_{actor}_core" if actor == "customer" else f"dim_{clean_domain}_{actor}"
        fact_table_name = f"fact_{clean_domain}_{event}"

        actor_sk = f"{actor}_sk"
        actor_id = f"{actor}_id"
        actor_name = f"{actor}_name"
        event_id = f"{event[:-1] if event.endswith('s') else event}_id"

        dim_columns = [
            {"name": actor_sk, "type": "VARCHAR(64)", "nullable": False, "primary_key": True, "is_inferred": False},
            {"name": actor_id, "type": "VARCHAR(64)", "nullable": False, "is_inferred": False},
            {"name": actor_name, "type": "VARCHAR(255)", "nullable": False, "is_inferred": False},
        ]

        if temporal_strategy in ["SCD2", "BITEMPORAL", "SCD2_HISTORICAL", "BITEMPORAL_VALID_AND_SYSTEM_TIME"]:
            dim_columns.extend([
                {"name": "scd_valid_from", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False},
                {"name": "scd_valid_to", "type": "TIMESTAMPTZ", "nullable": False, "is_inferred": False, "default": "'9999-12-31 UTC'"},
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"},
                {"name": "is_inferred", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "FALSE"}
            ])

        fact_columns = [
            {"name": event_id, "type": "BIGINT", "nullable": False, "primary_key": True, "is_inferred": False},
            {"name": actor_sk, "type": "VARCHAR(64)", "nullable": False, "foreign_key": f"{dim_table_name}.{actor_sk}", "is_inferred": False},
            {"name": "total_amount_usd", "type": "DECIMAL(14,2)", "nullable": False, "is_inferred": False},
            {"name": "estimated_delivery_days", "type": "INT", "nullable": True, "is_inferred": True}
        ]

        if is_multi_currency:
            fact_columns.extend([
                {"name": "amount_local", "type": "DECIMAL(14,2)", "nullable": False},
                {"name": "currency_code", "type": "VARCHAR(3)", "nullable": False},
                {"name": "exchange_rate_to_usd", "type": "DECIMAL(12,6)", "nullable": False}
            ])

        tables = [
            {
                "name": dim_table_name,
                "type": "DIMENSION",
                "is_conformed": True,
                "primary_key": actor_sk,
                "cluster_by": [actor_sk],
                "columns": dim_columns
            },
            {
                "name": fact_table_name,
                "type": "FACT",
                "primary_key": event_id,
                "partition_by": "order_date_key",
                "cluster_by": [actor_sk],
                "columns": fact_columns
            }
        ]

        # 4. Optional Secondary Dimension (Location / Facility)
        if raw_location and raw_location.lower() != actor:
            loc = re.sub(r"[^a-z0-9_]", "", raw_location.lower())
            loc_table_name = f"dim_{clean_domain}_{loc}"
            loc_sk = f"{loc}_sk"
            loc_id = f"{loc}_id"
            loc_name = f"{loc}_name"

            tables.append({
                "name": loc_table_name,
                "type": "DIMENSION",
                "is_conformed": True,
                "primary_key": loc_sk,
                "columns": [
                    {"name": loc_sk, "type": "VARCHAR(64)", "nullable": False, "primary_key": True},
                    {"name": loc_id, "type": "VARCHAR(64)", "nullable": False},
                    {"name": loc_name, "type": "VARCHAR(255)", "nullable": False}
                ]
            })
            # Attach foreign key to fact
            fact_columns.append({
                "name": loc_sk,
                "type": "VARCHAR(64)",
                "nullable": True,
                "foreign_key": f"{loc_table_name}.{loc_sk}",
                "is_inferred": True
            })

        return {
            "domain": clean_domain,
            "temporal_strategy": temporal_strategy,
            "pattern": pattern,
            "tables": tables
        }
