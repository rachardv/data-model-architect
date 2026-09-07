import re
from typing import Dict, Any, List, Optional
from src.schema_types import SchemaSpec, TableSpec, ColumnSpec, RelationshipSpec

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
        if "schema_spec" in user_request:
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
                "columns": dim_columns
            },
            {
                "name": fact_table_name,
                "type": "FACT",
                "primary_key": event_id,
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
