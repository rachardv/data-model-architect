import re
from typing import Dict, Any, List, Optional
from src.schema_types import SchemaSpec, TableSpec, ColumnSpec, RelationshipSpec
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

        # 2. Check for Factless Fact Table (Event Attendance / Coverage Matrix)
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
                {"name": "is_current", "type": "BOOLEAN", "nullable": False, "is_inferred": False, "default": "TRUE"}
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
