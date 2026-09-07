import re
from typing import Dict, List, Any, Optional

class NounVerbSemanticParser:
    """
    Domain-Driven Design (DDD) parser that:
    1. Decomposes raw business workflow text into Dimensions (Nouns), Facts (Verbs), and Statuses (Adjectives).
    2. Performs deterministic Semantic Role Labeling (SRL) for dynamic question generation.
    3. Generates 100% Plain-English, Non-Technical Business Discovery Questions for stakeholders.
    4. Infers technical database parameters directly from enriched business language narratives.
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
    def extract_domain_roles(narrative: str, parsed_entities: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        Performs deterministic Domain-Driven Semantic Role Labeling on the narrative.
        Maps domain entities into 5 semantic roles:
        - primary_event: Core transactional activity/event
        - primary_actor: Animate citizen, customer, patient, user
        - resource_location: Physical or logical facility, office, station
        - child_entity: Sub-unit, pallet, service, test, dish, line item
        - secondary_events: Other candidate event nouns (e.g. fee, payment)
        - secondary_actors: Other actors (e.g. examiner, doctor, clerk)
        - secondary_resources: Other resources (e.g. counter, dock, bay)
        """
        text = narrative.lower()
        words = [re.sub(r"[^a-z0-9]", "", w) for w in text.split()]
        words = [w for w in words if w]

        actor_seeds = {
            "driver", "drivers", "customer", "customers", "patient", "patients", "student", "students",
            "user", "users", "client", "clients", "employee", "employees", "borrower", "borrowers",
            "passenger", "passengers", "applicant", "applicants", "doctor", "doctors", "examiner", "examiners",
            "member", "members", "shopper", "shoppers", "guest", "guests", "citizen", "citizens", "clerk", "clerks",
            "carrier", "teacher", "teachers", "physician", "physicians", "nurse", "nurses", "agent", "agents"
        }
        
        event_seeds = {
            "appointment", "appointments", "slot", "slots", "order", "orders", "claim", "claims",
            "ticket", "tickets", "visit", "visits", "booking", "bookings", "reservation", "reservations",
            "encounter", "encounters", "admission", "admissions", "enrollment", "enrollments",
            "purchase", "purchases", "sale", "sales", "transaction", "transactions", "flight", "flights",
            "shipment", "shipments", "delivery", "deliveries", "case", "cases", "lesson", "lessons",
            "exam", "exams", "test", "tests", "payment", "payments", "fee", "fees", "refund", "refunds"
        }

        resource_seeds = {
            "office", "offices", "warehouse", "warehouses", "store", "stores", "clinic", "clinics",
            "hospital", "hospitals", "branch", "branches", "counter", "counters", "dock", "docks",
            "bay", "bays", "station", "stations", "terminal", "terminals", "school", "schools",
            "university", "universities", "department", "departments", "center", "centers", "facility", "facilities"
        }

        child_seeds = {
            "item", "items", "pallet", "pallets", "cargo", "dish", "dishes", "meal", "meals",
            "prescription", "prescriptions", "package", "packages", "service", "services",
            "procedure", "procedures", "question", "questions", "part", "parts"
        }

        inanimate_er_words = {
            "number", "order", "paper", "water", "tier", "layer", "letter", "quarter",
            "center", "meter", "server", "cluster", "container", "buffer", "header",
            "footer", "manner", "matter", "power", "weather", "ledger", "calendar"
        }

        found_actors = [w for w in words if w in actor_seeds]
        if not found_actors:
            found_actors = [
                w for w in words 
                if len(w) > 4 and (w.endswith("er") or w.endswith("or") or w.endswith("ee")) 
                and w not in event_seeds and w not in resource_seeds and w not in inanimate_er_words
            ]

        found_events = [w for w in words if w in event_seeds]
        if not found_events:
            found_events = [
                w for w in words 
                if len(w) > 5 and (w.endswith("ment") or w.endswith("tion") or w.endswith("ing")) 
                and w not in actor_seeds and w not in resource_seeds and w not in inanimate_er_words
            ]

        found_resources = [w for w in words if w in resource_seeds]
        found_children = [w for w in words if w in child_seeds]

        # Compound domain entity handling
        if "appointment" in text and "slot" in text:
            primary_event = "appointment slot"
        elif found_events:
            cand = found_events[0]
            primary_event = cand.rstrip("s") if cand.endswith("s") and not cand.endswith("ss") else cand
        else:
            primary_event = "transaction"

        if any(k in text for k in ["driver license", "driver licence", "licence office", "license office", "dmv"]):
            resource_loc = "driver license office"
        elif found_resources:
            cand = found_resources[0]
            resource_loc = cand.rstrip("s") if cand.endswith("s") and not cand.endswith("ss") else cand
        else:
            resource_loc = "location"

        if found_actors:
            cand = found_actors[0]
            primary_actor = cand.rstrip("s") if cand.endswith("s") and not cand.endswith("ss") else cand
        else:
            primary_actor = "user"

        if found_children:
            cand = found_children[0]
            child_item = cand.rstrip("s") if cand.endswith("s") and not cand.endswith("ss") else cand
        else:
            child_item = "item / sub-unit"

        sec_events = [e for e in set(found_events) if e.rstrip("s") != primary_event.rstrip("s")]
        sec_actors = [a for a in set(found_actors) if a.rstrip("s") != primary_actor.rstrip("s")]
        sec_resources = [r for r in set(found_resources) if r.rstrip("s") != resource_loc.rstrip("s")]

        return {
            "primary_event": primary_event,
            "primary_actor": primary_actor,
            "resource_location": resource_loc,
            "child_entity": child_item,
            "secondary_events": sorted(sec_events),
            "secondary_actors": sorted(sec_actors),
            "secondary_resources": sorted(sec_resources)
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
            "instant updates", "powers a live", "powers the live", "microservice", "real time app",
            "shopping cart", "session token", "point-of-care", "ehr", "bedside charting"
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
