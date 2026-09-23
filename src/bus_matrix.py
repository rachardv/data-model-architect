from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class BusMatrixDimension(BaseModel):
    name: str
    key: str
    is_role_playing: bool = False
    roles: List[str] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)

class BusMatrixFact(BaseModel):
    name: str
    grain: str
    metric_columns: List[str] = Field(default_factory=list)
    dimension_keys: List[str] = Field(default_factory=list)

class BusMatrix(BaseModel):
    domain: str
    facts: List[BusMatrixFact] = Field(default_factory=list)
    dimensions: List[BusMatrixDimension] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """
        Renders the standard Ralph Kimball Enterprise Bus Matrix 2D grid in Markdown.
        Rows: Business Process Fact Tables.
        Columns: Conformed Dimensions.
        """
        if not self.facts or not self.dimensions:
            return "*(Empty Bus Matrix)*"

        headers = ["Business Process (Fact Table)", "Fact Grain"] + [d.name for d in self.dimensions]
        sep = [" :--- "] * len(headers)
        lines = [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join(sep) + "|"
        ]

        for f in self.facts:
            row = [f"**`{f.name}`**", f.grain]
            for d in self.dimensions:
                # Check participation
                matching_keys = [k for k in f.dimension_keys if k == d.key or k in d.roles]
                if matching_keys:
                    if d.is_role_playing and any(k in d.roles for k in matching_keys):
                        role_name = next(k for k in matching_keys if k in d.roles)
                        row.append(f"✓ (`{role_name}`)")
                    else:
                        row.append("✓ (Conformed)")
                else:
                    row.append("—")
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def generate_drill_across_sql(
        self,
        fact_a_name: Optional[str] = None,
        fact_b_name: Optional[str] = None,
        common_keys: Optional[List[str]] = None
    ) -> str:
        """
        Synthesizes the standard Ralph Kimball Drill-Across SQL pattern:
        Aggregates each fact table independently in a CTE to the common grain,
        then performs a FULL OUTER JOIN on conformed dimension keys.
        Prevents Chasm Traps and Cartesian inflation.
        """
        if len(self.facts) < 2:
            return "-- Minimum 2 fact tables required for Drill-Across query generation."

        fa = next((f for f in self.facts if f.name == fact_a_name), self.facts[0])
        fb = next((f for f in self.facts if f.name == fact_b_name), self.facts[1])

        # Discover common dimension keys
        if not common_keys:
            # Map role-playing date keys to generic date_sk for grouping
            fa_keys = set(fa.dimension_keys)
            fb_keys = set(fb.dimension_keys)
            shared_exact = list(fa_keys.intersection(fb_keys))
            common_keys = shared_exact if shared_exact else ["customer_sk"]

        metric_a = fa.metric_columns[0] if fa.metric_columns else "amount_usd"
        metric_b = fb.metric_columns[0] if fb.metric_columns else "amount_usd"

        group_cols = ", ".join(common_keys)
        join_clauses = " AND ".join([f"a.{k} = b.{k}" for k in common_keys])
        coalesce_cols = ",\n    ".join([f"COALESCE(a.{k}, b.{k}) AS {k}" for k in common_keys])

        return f"""WITH {fa.name}_agg AS (
    SELECT 
        {group_cols},
        SUM({metric_a}) AS total_{metric_a}
    FROM {fa.name}
    GROUP BY {group_cols}
),
{fb.name}_agg AS (
    SELECT 
        {group_cols},
        SUM({metric_b}) AS total_{metric_b}
    FROM {fb.name}
    GROUP BY {group_cols}
)
SELECT 
    {coalesce_cols},
    COALESCE(a.total_{metric_a}, 0.0) AS total_{metric_a},
    COALESCE(b.total_{metric_b}, 0.0) AS total_{metric_b}
FROM {fa.name}_agg a
FULL OUTER JOIN {fb.name}_agg b 
    ON {join_clauses};"""

class BusMatrixSynthesizer:
    """
    Constructs multi-fact Enterprise Bus Matrices with conformed dimensions.
    """

    @classmethod
    def synthesize_bus_matrix(
        cls,
        domain: str,
        actor: str = "customer",
        events: Optional[List[str]] = None
    ) -> BusMatrix:
        clean_domain = domain.lower().replace(" ", "_").replace("-", "_")
        clean_actor = actor.lower().replace(" ", "_").replace("-", "_")

        # Standardize events
        if not events:
            raw_events = ["orders", "shipments", "payments"]
        else:
            raw_events = []
            for e in events:
                ce = e.lower().strip()
                if not ce.endswith("s") and not ce.endswith("ss"):
                    ce += "s"
                if ce not in raw_events:
                    raw_events.append(ce)
            if len(raw_events) < 2:
                raw_events = ["orders", "shipments", "payments"]

        actor_dim_name = f"dim_{clean_domain}_{clean_actor}_core" if clean_actor == "customer" else f"dim_{clean_domain}_{clean_actor}"
        actor_sk = f"{clean_actor}_sk"

        dim_actor = BusMatrixDimension(
            name=actor_dim_name,
            key=actor_sk,
            is_role_playing=False,
            attributes=[f"{clean_actor}_id", f"{clean_actor}_name", "tier", "region"]
        )

        dim_product = BusMatrixDimension(
            name=f"dim_{clean_domain}_product",
            key="product_sk",
            is_role_playing=False,
            attributes=["product_id", "product_name", "category", "unit_price"]
        )

        dim_date = BusMatrixDimension(
            name="dim_date",
            key="date_sk",
            is_role_playing=True,
            roles=["order_date_key", "ship_date_key", "payment_date_key"],
            attributes=["calendar_date", "year", "month", "quarter", "day_of_week"]
        )

        dimensions = [dim_actor, dim_product, dim_date]
        facts: List[BusMatrixFact] = []

        for ev in raw_events:
            sing_ev = ev[:-1] if ev.endswith("s") else ev
            fact_name = f"fact_{clean_domain}_{ev}"
            
            if "order" in ev or "sale" in ev:
                facts.append(BusMatrixFact(
                    name=fact_name,
                    grain=f"1 row per {sing_ev} line item",
                    metric_columns=["total_amount_usd", "quantity"],
                    dimension_keys=[actor_sk, "product_sk", "order_date_key"]
                ))
            elif "ship" in ev or "fulfill" in ev or "deliver" in ev:
                facts.append(BusMatrixFact(
                    name=fact_name,
                    grain=f"1 row per {sing_ev} package",
                    metric_columns=["shipping_cost_usd"],
                    dimension_keys=[actor_sk, "product_sk", "ship_date_key"]
                ))
            elif "pay" in ev or "settle" in ev or "bill" in ev:
                facts.append(BusMatrixFact(
                    name=fact_name,
                    grain=f"1 row per {sing_ev} transaction attempt",
                    metric_columns=["payment_amount_usd"],
                    dimension_keys=[actor_sk, "payment_date_key"]
                ))
            else:
                facts.append(BusMatrixFact(
                    name=fact_name,
                    grain=f"1 row per {sing_ev} event",
                    metric_columns=[f"{sing_ev}_amount_usd"],
                    dimension_keys=[actor_sk, f"{sing_ev}_date_key"]
                ))

        return BusMatrix(
            domain=clean_domain,
            facts=facts,
            dimensions=dimensions
        )
