from typing import Dict, List, Any

class NounVerbSemanticParser:
    """
    Domain-Driven Design (DDD) parser that:
    1. Decomposes raw business workflow text into Dimensions (Nouns), Facts (Verbs), and Statuses (Adjectives).
    2. Generates 100% Plain-English, Non-Technical Business Discovery Questions for stakeholders.
    3. Infers technical database parameters directly from enriched business language narratives.
    """
    
    @staticmethod
    def parse_workflow_narrative(narrative: str) -> Dict[str, List[str]]:
        words = [w.strip(".,;:()\"'").lower() for w in narrative.split()]
        
        # Core domain taxonomy seeds
        noun_indicators = {
            "customer", "employee", "product", "department", "manager", "order",
            "claim", "patient", "driver", "warehouse", "store", "account",
            "item", "cart", "ticket", "invoice", "payment", "shipment", "carrier",
            "doctor", "hospital", "part", "supplier", "tenant", "subscription"
        }
        verb_indicators = {
            "places", "orders", "promotes", "transfers", "pays", "ships",
            "delivers", "refunds", "charges", "admits", "executes", "buys",
            "cancels", "submits", "upgrades", "downgrades", "scans", "picks"
        }
        adjective_indicators = {
            "active", "remote", "shipped", "pending", "cancelled", "approved",
            "high", "low", "returned", "closed", "incurred", "allocated"
        }
        
        extracted_nouns = sorted(list({w for w in words if w in noun_indicators or w.endswith("er") or w.endswith("ee") or w.endswith("ment") or w.endswith("or")}))
        extracted_verbs = sorted(list({w for w in words if w in verb_indicators or w.endswith("s") or w.endswith("ed") or w.endswith("ing")}))
        extracted_adjectives = sorted(list({w for w in words if w in adjective_indicators or w.endswith("able") or w.endswith("ed")}))
        
        return {
            "dimensions_nouns": extracted_nouns,
            "facts_verbs": extracted_verbs,
            "statuses_adjectives": extracted_adjectives
        }

    @staticmethod
    def generate_business_discovery_questions(narrative: str) -> List[Dict[str, Any]]:
        """
        Generates 100% non-technical, business-friendly questions to clarify 
        workload intent, history requirements, and process lifecycle.
        """
        return [
            {
                "id": "q_workload_intent",
                "question": "How will your business teams or applications primarily use this data?",
                "options": [
                    "(Recommended) We want to build executive dashboards, BI reports, and analyze sales/performance trends over time.",
                    "This directly powers a live user-facing website, mobile app, or checkout screen where speed and instant updates are critical.",
                    "We are collecting continuous high-frequency data from sensors, live tracking devices, or financial market tickers every second."
                ]
            },
            {
                "id": "q_history_policy",
                "question": "When a customer, store, or supplier updates their profile (like moving to a new address), how should past business reports look?",
                "options": [
                    "(Recommended) Past historical reports should preserve the original address at the time of each transaction so past regional sales remain accurate.",
                    "Always overwrite past records with their newest address everywhere.",
                    "We are legally/financially regulated (SOX, Banking) and need to prove exactly what our accounting records showed on any past audit date."
                ]
            },
            {
                "id": "q_process_stages",
                "question": "Does this business process involve multiple sequential steps where you need to track turnaround time?",
                "options": [
                    "(Recommended) Yes, we need to track how long it takes to move across stages (e.g. from Order Placed -> Picked in Warehouse -> Shipped -> Delivered).",
                    "No, we only need to record each individual transaction as a single standalone event.",
                    "We need periodic daily or monthly summary snapshots of balances, inventory stock, or revenue."
                ]
            }
        ]

    @staticmethod
    def infer_parameters_from_business_narrative(enriched_narrative: str) -> Dict[str, bool]:
        """
        Translates rich, plain-English business narratives into exact technical 
        flags for the DataModelDecisionEngine without exposing jargon to the user.
        """
        text = enriched_narrative.lower()
        
        # 1. High-frequency Streaming Telemetry
        is_stream = any(k in text for k in [
            "sensor", "telemetry", "iot", "ticker", "every second",
            "milliseconds", "streaming", "clickstream", "devices"
        ])
        
        # 2. Live Application (OLTP)
        is_live_app = any(k in text for k in [
            "live website", "mobile app", "checkout screen", "user clicks",
            "instant updates", "powers a live", "microservice", "real time app",
            "shopping cart", "session token"
        ])
        
        # 3. Temporal History Requirements (SCD2 / Audit)
        needs_history = not any(k in text for k in [
            "always overwrite", "current state only", "overwrite past records"
        ])
        
        # 4. Retroactive Auditing / SOX / Backdating
        has_retroactive_backdating = any(k in text for k in [
            "sox", "regulated", "audit date", "retroactive", "backdated",
            "restatement", "general ledger", "accounting audit"
        ])
        
        # 5. Multi-Stage Milestones / Lifecycles
        has_multi_stage_milestones = any(k in text for k in [
            "sequential steps", "turnaround time", "order placed ->", "milestone",
            "stage", "duration", "lifecycle", "placed -> picked", "admission-to-discharge",
            "funnel", "intake -> underwriting -> closing"
        ])
        
        # 6. Periodic State Rollups / Snapshots
        is_periodic_state_rollup = any(k in text for k in [
            "snapshot", "monthly summary", "daily summary", "inventory stock",
            "balance rollup", "month-end", "nightly snapshot"
        ])
        
        # 7. Volatile ML Scores / Health Bands
        has_high_churn_ml_scores = any(k in text for k in [
            "ml score", "churn risk", "health score", "fico", "propensity",
            "dynamic score", "daily risk scoring", "updating nightly"
        ])
        
        return {
            "is_live_app": is_live_app,
            "is_high_frequency_stream": is_stream,
            "needs_history": needs_history,
            "has_retroactive_backdating": has_retroactive_backdating,
            "has_multi_stage_milestones": has_multi_stage_milestones,
            "is_periodic_state_rollup": is_periodic_state_rollup,
            "has_high_churn_ml_scores": has_high_churn_ml_scores
        }
