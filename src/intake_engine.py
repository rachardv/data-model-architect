import re
from typing import Dict, List, Any, Optional
from src.noun_verb_parser import NounVerbSemanticParser
from src.decision_engine import DataModelDecisionEngine

class SemanticSanityFilter:
    """
    Validates business narratives against low-entropy gibberish, 
    insufficient descriptions, and semantic logical contradictions.
    """
    
    COMMON_WORDS = {"a", "at", "as", "all", "ask", "fall", "flask", "glad", "flag", "salt", "walk", "talk", "dash", "flash"}
    
    @classmethod
    def validate_narrative(cls, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        words = cleaned.split()
        
        # 1. Minimum Word Count Check
        if len(words) < 4:
            return {
                "valid": False,
                "reason": "REJECT_INSUFFICIENT_LENGTH",
                "message": "Input is too brief. Please provide a descriptive business narrative (minimum 4 words)."
            }
            
        # 2. Gibberish / Repetitive Character Check
        for w in words:
            w_clean = re.sub(r"[^a-zA-Z]", "", w.lower())
            if not w_clean:
                continue
                
            # Check 4+ repeated identical characters (e.g. 'aaaa', 'zzzz')
            if re.search(r"(.)\1{3,}", w_clean):
                return {
                    "valid": False,
                    "reason": "REJECT_GIBBERISH_DETECTED",
                    "message": f"Repetitive meaningless text detected: '{w}'. Please describe real business entities."
                }
                
            # Check words of length >= 4 that are known keyboard mash patterns
            if len(w_clean) >= 4 and w_clean not in cls.COMMON_WORDS:
                if re.match(r"^(asdf|lkjh|qwerty|zxcv|ghjk)", w_clean):
                    return {
                        "valid": False,
                        "reason": "REJECT_GIBBERISH_DETECTED",
                        "message": f"Keyboard mash pattern detected: '{w}'."
                    }
                # Words >= 5 chars with zero vowels
                if len(w_clean) >= 5 and not any(v in w_clean for v in "aeiouy"):
                    return {
                        "valid": False,
                        "reason": "REJECT_GIBBERISH_DETECTED",
                        "message": f"Non-pronounceable gibberish with no vowels: '{w}'."
                    }
                    
        # 3. Contradiction & Conflict Detection
        lower_text = cleaned.lower()
        has_oltp_marker = any(k in lower_text for k in ["sub-millisecond", "row lock", "live checkout cart", "mobile app backend", "instant point updates"])
        has_monthly_rollup_marker = any(k in lower_text for k in ["monthly snapshot", "monthly balance rollup", "month-end accounting ledger"])
        has_high_freq_sensor_marker = any(k in lower_text for k in ["streaming sensor", "iot telemetry every second", "10,000 ticks per second"])
        
        if has_oltp_marker and has_monthly_rollup_marker:
            return {
                "valid": False,
                "reason": "FLAG_CONTRADICTION",
                "message": "Contradiction detected: Narrative requests both sub-millisecond operational row-locking (OLTP) and monthly batch accounting snapshots (OLAP). Clarification needed."
            }
            
        if has_oltp_marker and has_high_freq_sensor_marker:
            return {
                "valid": False,
                "reason": "FLAG_CONTRADICTION",
                "message": "Contradiction detected: Narrative mixes live point-of-care CRUD with high-frequency streaming IoT telemetry. Clarification needed."
            }
            
        return {
            "valid": True,
            "reason": "SANITY_PASSED",
            "message": "Semantic sanity validation successful."
        }


class IntakeCompletenessScorer:
    """
    Evaluates the 5 Mandatory Architectural Vectors required to reliably design a data model:
    1. Workload Intent (Reporting / BI vs. Live App vs. Stream) - 20%
    2. Entity Grain (What do you sell / what is 1 row of activity?) - 20%
    3. Temporal History Policy (Preserve history vs. In-place overwrite) - 20%
    4. Lifecycle Funnel (Multi-stage turnaround vs. Single transaction vs. Monthly snapshot) - 20%
    5. Relationship Multiplicity (1:1 / 1:N vs. Shared Co-ownership M:N) - 20%
    
    STRICT RULE: Completeness must reach exactly 100.0% before outputting specs.
    """
    
    VECTOR_WEIGHTS = {
        "workload_intent": 20.0,
        "entity_grain": 20.0,
        "temporal_policy": 20.0,
        "lifecycle_funnel": 20.0,
        "relationship_multiplicity": 20.0
    }
    
    @classmethod
    def score_completeness(cls, enriched_narrative: str, parsed_entities: Dict[str, List[str]]) -> Dict[str, Any]:
        text = enriched_narrative.lower()
        resolved_vectors = {}
        missing_vectors = []
        
        # Vector 1: Workload Intent
        workload_keywords = [
            "dashboard", "reporting", "bi report", "analytics", "trends over time",
            "live website", "mobile app", "checkout", "sensor", "telemetry", "streaming",
            "ticker", "live point-of-care", "ehr application", "powers the live",
            "powers a live", "real-time", "bedside charting", "operational database",
            "sub-second", "live app", "point-of-care", "analyze", "metrics", "performance",
            "over time", "business metrics"
        ]
        if any(k in text for k in workload_keywords):
            resolved_vectors["workload_intent"] = True
        else:
            resolved_vectors["workload_intent"] = False
            missing_vectors.append("workload_intent")
            
        # Vector 2: Entity Grain & Offering
        nouns = parsed_entities.get("dimensions_nouns", [])
        grain_keywords = [
            "line item", "order line", "transaction", "each encounter", "single event",
            "snapshot", "one row per", "individual", "prescription", "procedure",
            "order", "patient", "stay", "admission", "vitals", "product sales",
            "physical or digital goods", "subscription memberships", "monthly billing renewals",
            "patient care", "credit lending", "revenue", "insurance", "car insurance",
            "policy", "driver", "coverage", "premium"
        ]
        if len(nouns) >= 2 and any(k in text for k in grain_keywords):
            resolved_vectors["entity_grain"] = True
        elif len(nouns) >= 3 or any(k in text for k in ["product sales", "physical or digital goods", "subscription memberships", "patient care", "credit lending"]):
            resolved_vectors["entity_grain"] = True
        else:
            resolved_vectors["entity_grain"] = False
            missing_vectors.append("entity_grain")
            
        # Vector 3: Temporal History Policy
        temporal_keywords = [
            "preserve", "historical", "scd", "original address", "point-in-time",
            "overwrite", "newest address", "audit date", "regulated", "sox",
            "insurance at time", "newest policy", "always overwrite", "newest menu price",
            "original price"
        ]
        if any(k in text for k in temporal_keywords):
            resolved_vectors["temporal_policy"] = True
        else:
            resolved_vectors["temporal_policy"] = False
            missing_vectors.append("temporal_policy")
            
        # Vector 4: Lifecycle Funnel
        lifecycle_keywords = [
            "stage", "milestone", "turnaround", "placed ->", "duration", "funnel",
            "sequential", "standalone event", "single event", "encounter",
            "picked to shipped", "admitted", "discharged", "inpatient stay",
            "admission to discharge", "stay", "transferred", "purchase", "checkout counter",
            "point-of-sale", "sale", "sales", "checkout", "snapshot", "snapshots",
            "periodic", "monthly summary", "daily summary", "balance rollup", "stock levels",
            "single standalone transaction", "multi-stage turnaround tracking"
        ]
        if any(k in text for k in lifecycle_keywords):
            resolved_vectors["lifecycle_funnel"] = True
        else:
            resolved_vectors["lifecycle_funnel"] = False
            missing_vectors.append("lifecycle_funnel")
            
        # Vector 5: Relationship Multiplicity
        if len(nouns) >= 2 or any(k in text for k in ["one-to-one ownership", "one-to-many", "co-ownership", "shared", "standard"]):
            resolved_vectors["relationship_multiplicity"] = True
        else:
            resolved_vectors["relationship_multiplicity"] = False
            missing_vectors.append("relationship_multiplicity")
            
        score = sum(cls.VECTOR_WEIGHTS[k] for k, v in resolved_vectors.items() if v)
        
        # STRICT 100.0% COMPLETENESS HARD GATE
        is_sufficient = (score >= 100.0)
        
        return {
            "completeness_score": score,
            "is_sufficient": is_sufficient,
            "resolved_vectors": [k for k, v in resolved_vectors.items() if v],
            "missing_vectors": missing_vectors
        }


class AdaptiveBusinessInterviewer:
    """
    Dynamically conducts natural, consultative business discovery interviews.
    Translates technical architecture gaps into 100% natural, human-friendly business questions
    and explicitly includes bracketed explanations of what technical decision each question determines.
    """
    
    QUESTION_BANK = {
        "workload_intent": {
            "id": "q_workload_intent",
            "question": "How will your team or end-users primarily interact with this system? [Determines: Whether to build an Analytical Reporting Warehouse (OLAP), a Live User-Facing App (OLTP), or a Streaming Pipeline]",
            "options": [
                "(Recommended) We want to build executive dashboards, BI reports, and analyze business trends over time.",
                "This directly powers a live customer-facing app, website, point-of-care EHR, or checkout screen where instant sub-second updates are critical.",
                "We are collecting continuous real-time data streams from sensors, tracking devices, or market tickers every second."
            ]
        },
        "entity_grain": {
            "id": "q_entity_grain",
            "question": "What does your company primarily sell or provide, and what is the primary activity you want to measure? [Determines: The atomic grain of your primary Fact Table and the core business metrics/KPIs to calculate]",
            "options": [
                "(Recommended) Detailed product sales & shopping cart line items (e.g. customers buying physical or digital goods).",
                "Recurring subscription memberships & monthly billing renewals (e.g. SaaS software, gym memberships, subscriptions).",
                "Healthcare & clinical patient care (e.g. hospital admissions, doctor visits, medication prescriptions).",
                "Financial lending & banking accounts (e.g. commercial business loans, deposits, mortgage applications)."
            ]
        },
        "temporal_policy": {
            "id": "q_temporal_policy",
            "question": "When a customer, store, or patient updates their profile (like moving to a new address), how should historical reports behave? [Determines: Historical time-travel tracking (SCD Type 2 with effective dates) vs simple in-place overwriting (SCD Type 1)]",
            "options": [
                "(Recommended) Historical reports should preserve their original address and profile at the exact time of each event so past regional sales remain accurate (SCD Type 2).",
                "Always overwrite past records with their newest address and profile everywhere across the system (SCD Type 1).",
                "We are strictly regulated (SOX, Banking, HIPAA) and need to prove exactly what our accounting/clinical records showed on any historical audit date."
            ]
        },
        "lifecycle_funnel": {
            "id": "q_lifecycle_funnel",
            "question": "Does this business workflow involve tracking turnaround time across multiple sequential stages? [Determines: Accumulating Snapshot Fact Table with milestone date foreign keys vs discrete single-event Transaction Fact Table]",
            "options": [
                "(Recommended) Yes, multi-stage turnaround tracking (e.g. from Order Placed -> Picked -> Shipped -> Delivered, or Loan Applied -> Approved -> Funded).",
                "No, single standalone transaction events (e.g. discrete store sales, point-of-sale receipt scans).",
                "Periodic state summary rollups (e.g. monthly balance snapshots, daily warehouse inventory counts)."
            ]
        },
        "relationship_multiplicity": {
            "id": "q_relationship_multiplicity",
            "question": "In your day-to-day operations, do multiple people share accounts, or can an order/case involve multiple primary owners? [Determines: Standard 1:N foreign keys vs a multi-valued Bridge Table to prevent accidental revenue double-counting]",
            "options": [
                "(Recommended) Standard one-to-one ownership (e.g. 1 customer per order, 1 primary owner per account).",
                "Shared co-ownership (e.g. joint bank accounts with multiple co-signers, patient cases with multiple attending doctors)."
            ]
        }
    }
    
    @staticmethod
    def _pluralize(word: str) -> str:
        w = word.strip()
        if not w:
            return w
        parts = w.split()
        last = parts[-1]
        if last.endswith("s") or last.endswith("x") or last.endswith("ch") or last.endswith("sh"):
            pl_last = last + "es"
        elif last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
            pl_last = last[:-1] + "ies"
        else:
            pl_last = last + "s"
        parts[-1] = pl_last
        return " ".join(parts)

    @classmethod
    def build_dynamic_question(cls, vector_name: str, domain_roles: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not domain_roles:
            return cls.QUESTION_BANK.get(vector_name, {})

        event = domain_roles.get("primary_event", "transaction")
        events_pl = cls._pluralize(event)
        actor = domain_roles.get("primary_actor", "user")
        actors_pl = cls._pluralize(actor)
        loc = domain_roles.get("resource_location", "location")
        locs_pl = cls._pluralize(loc)
        child = domain_roles.get("child_entity", "item / sub-unit")
        child_pl = cls._pluralize(child)
        sec_events = domain_roles.get("secondary_events", [])

        if vector_name == "workload_intent":
            return {
                "id": "q_workload_intent",
                "question": f"How will your team or end-users primarily interact with this {event} system? [Determines: Whether to build an Analytical Reporting Warehouse (OLAP), a Live User-Facing App (OLTP), or a Streaming Pipeline]",
                "options": [
                    f"(Recommended - OLAP) Analytical reporting & executive dashboards: Analyzing historical trends, {event} availability rates, and performance over time across {locs_pl}.",
                    f"(OLTP) Live customer-facing application: Directly powering the portal or screen where {actors_pl} search, create, and update {events_pl} with instant sub-second response times.",
                    f"(Streaming) Real-time event streams: Collecting continuous high-frequency status pings, telemetry, or ticker updates every second."
                ]
            }

        elif vector_name == "entity_grain":
            options = [
                f"(Recommended - Event Header) One row per {event}: Tracking total counts, status, and utilization by {actor} and {loc}.",
                f"(Line-Item Detail) One row per {child} inside each {event}: If a single {event} contains multiple distinct components requiring separate breakdown.",
                f"(State Change) One row per status update: Recording every milestone or state transition as a {event} progresses from start to finish."
            ]
            if sec_events:
                sec_ev = sec_events[0].rstrip("s")
                options.append(
                    f"Multi-Fact Bus Matrix: Build coordinated separate fact tables (e.g. fact_{event.replace(' ', '_')} and fact_{sec_ev.replace(' ', '_')}) sharing conformed dimensions ({loc}, {actor}) to avoid chasm traps."
                )
            return {
                "id": "q_entity_grain",
                "question": f"When your team pulls up a report or spreadsheet of {events_pl}, what should each single row represent? [Determines: The atomic grain of your primary Fact Table and the core business metrics/KPIs to calculate]",
                "options": options
            }

        elif vector_name == "temporal_policy":
            return {
                "id": "q_temporal_policy",
                "question": f"When a {loc} or {actor} updates their profile (such as operating hours, address, or capacity), how should historical reports behave? [Determines: Historical time-travel tracking (SCD Type 2 with effective dates) vs simple in-place overwriting (SCD Type 1)]",
                "options": [
                    f"(Recommended - SCD Type 2) Historical reports should preserve the original {loc} profile at the exact time of each {event} so past utilization and regional reports remain 100% accurate (SCD Type 2).",
                    f"(SCD Type 1) Always overwrite past records with their newest {loc} details everywhere across the system (SCD Type 1).",
                    f"(Bi-Temporal / Regulatory Audit) We are strictly regulated (Government, SOX, Banking, HIPAA) and need to prove exactly what records showed on any historical audit date."
                ]
            }

        elif vector_name == "lifecycle_funnel":
            return {
                "id": "q_lifecycle_funnel",
                "question": f"How does your team need to measure and report on {events_pl} over time? [Determines: Accumulating Snapshot Fact Table with milestone date foreign keys vs Periodic Snapshot vs discrete Transaction Fact Table]",
                "options": [
                    f"(Recommended for capacity & availability) Periodic Daily Snapshots: One row per {loc} each day recording total capacity, open {events_pl}, and booked counts.",
                    f"(Transaction Fact) Discrete Point-in-Time Events: One row recorded each time an individual {event} is created, reserved, or cancelled.",
                    f"(Accumulating Funnel) Multi-Stage Turnaround: One row per {event} measuring turnaround duration across sequential stages."
                ]
            }

        elif vector_name == "relationship_multiplicity":
            return {
                "id": "q_relationship_multiplicity",
                "question": f"Can a single {event} involve multiple {actors_pl}, or is there always strictly 1 primary {actor} per {event}? [Determines: Standard 1:N foreign keys vs a multi-valued Bridge Table to prevent accidental double-counting]",
                "options": [
                    f"(Recommended) Standard one-to-one ownership: Exactly 1 primary {actor} per {event} (direct foreign key).",
                    f"Shared co-ownership: Multiple {actors_pl} can be attached to one {event} (requires a Kimball Bridge Table to avoid double-counting)."
                ]
            }

        return cls.QUESTION_BANK.get(vector_name, {})

    @classmethod
    def get_questions_for_missing_vectors(cls, missing_vectors: List[str], domain_roles: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if domain_roles:
            return [cls.build_dynamic_question(vec, domain_roles) for vec in missing_vectors if vec in cls.QUESTION_BANK]
        return [cls.QUESTION_BANK[vec] for vec in missing_vectors if vec in cls.QUESTION_BANK]
        
    @classmethod
    def generate_delta_entity_questions(cls, new_entity_name: str) -> List[Dict[str, Any]]:
        """
        Dynamically generates Kimball-compliant discovery questions with bracketed explanations
        whenever an unreferenced entity is introduced in Workflow 2.
        """
        return [
            {
                "id": f"q_{new_entity_name}_cardinality",
                "question": f"In your daily operations, can a single transaction/order be split across multiple {new_entity_name}s, or is there always strictly 1 primary {new_entity_name}? [Determines: Direct Foreign Key vs Kimball Multi-Valued Bridge Table for {new_entity_name}]",
                "options": [
                    f"(Recommended) Standard 1:1 {new_entity_name}: Exactly 1 {new_entity_name} per record.",
                    f"Multi-Valued Split: Multiple {new_entity_name}s can be attached to one record."
                ]
            },
            {
                "id": f"q_{new_entity_name}_scd",
                "question": f"When a {new_entity_name}'s profile, tier, or address updates, how should historical reports behave? [Determines: Slowly Changing Dimension (SCD) historical time-travel policy for {new_entity_name}]",
                "options": [
                    f"(Recommended) Preserve historical {new_entity_name} profile at the time of each transaction (SCD Type 2).",
                    f"Always overwrite past records with the newest {new_entity_name} profile everywhere (SCD Type 1)."
                ]
            }
        ]



class VectorConflictDetector:
    """
    Hybrid Deterministic Engine that audits newly submitted business rules against
    the 5 baseline architectural vectors. Detects vector breaks and generates
    plain-English impact alerts presenting Additive Expansion vs Full Refactor.
    """
    
    @classmethod
    def detect_conflicts(
        cls, 
        rules: List[Dict[str, Any]], 
        baseline_vectors: Dict[str, Any],
        existing_tables: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Audits rules for conflicts against baseline vectors:
        - entity_grain (e.g. order-header metrics on line-item grain)
        - relationship_multiplicity (e.g. multi-driver on 1:1 policy)
        - temporal_policy (e.g. SCD2 point-in-time audit on SCD1 table)
        - workload_intent (e.g. multi-year analytical warehouse queries on live OLTP table)
        - lifecycle_funnel (e.g. multi-stage turnaround tracking on single-event transaction fact)
        """
        conflicts = []
        
        for rule in rules:
            desc = rule.get("description", "").lower()
            definition = rule.get("definition", "").lower()
            combined = f"{desc} {definition}"
            
            # 1. Grain Conflict: Header metrics on Line-Item Grain
            current_grain = str(baseline_vectors.get("entity_grain", "LINE_ITEM")).upper()
            if any(g in current_grain for g in ["LINE_ITEM", "ATOMIC_LINE_ITEM", "ITEM_LINE", "LINE"]):
                header_indicators = ["shipping fee", "shipping amount", "total order discount", "order total", "cart total", "order tax", "basket level"]
                if any(ind in combined for ind in header_indicators):
                    conflicts.append({
                        "rule": rule.get("description"),
                        "vector_violated": "entity_grain",
                        "current_state": "Atomic Line-Item Grain (1 row per product sold)",
                        "rule_demands": "Order-Level Header Summary Metric",
                        "business_risk": "Risk of severe revenue and cost distortion (multiplying an order-level fee across multiple line-items inflates financial metrics)",
                        "additive_remedy": "Sprout an Order-Level Header Fact Mart (fact_orders_summary) sharing conformed dimensions",
                        "refactor_remedy": "Collapse the line-item fact into an order header fact table (permanently destroys product-level SKU analytics)"
                    })
                    
            # 2. Multiplicity Conflict: Multi-party / Co-ownership on 1:1 Schema
            current_multiplicity = str(baseline_vectors.get("relationship_multiplicity", "ONE_TO_ONE")).upper()
            if any(m in current_multiplicity for m in ["ONE_TO_ONE", "1:1", "ONE_TO_MANY"]):
                multi_indicators = ["multiple drivers", "co-driver", "co-signers", "joint owners", "shared account", "multiple owners", "up to 5 drivers", "co-borrower"]
                if any(ind in combined for ind in multi_indicators):
                    conflicts.append({
                        "rule": rule.get("description"),
                        "vector_violated": "relationship_multiplicity",
                        "current_state": "Standard 1:1 / 1:N Ownership (1 primary owner per account/policy)",
                        "rule_demands": "Multi-Valued Co-Ownership (M:N)",
                        "business_risk": "Risk of duplicate rows and false double-counting of policy premiums or account balances",
                        "additive_remedy": "Sprout a Kimball Multi-Valued Bridge Table (e.g. bridge_policy_drivers) to decouple co-owners without modifying existing foreign keys",
                        "refactor_remedy": "Deprecate existing foreign key and rebuild the entity graph with array columns or a new junction model"
                    })
                    
            # 3. Temporal Policy Conflict: Point-in-time Audit on SCD1
            current_temporal = str(baseline_vectors.get("temporal_policy", "SCD1_OVERWRITE")).upper()
            if any(t in current_temporal for t in ["SCD1", "SCD1_OVERWRITE", "OVERWRITE"]):
                temporal_indicators = ["preserve history", "point-in-time", "historical audit", "scd type 2", "scd2", "effective date", "never overwrite", "time-travel", "historical price at time"]
                if any(ind in combined for ind in temporal_indicators):
                    conflicts.append({
                        "rule": rule.get("description"),
                        "vector_violated": "temporal_policy",
                        "current_state": "SCD Type 1 (In-place overwrite of past records)",
                        "rule_demands": "SCD Type 2 Historical Time-Travel Tracking",
                        "business_risk": "Risk of non-compliance with audit regulations (SCD1 permanently destroys historical profile state)",
                        "additive_remedy": "Sprout an SCD2 Historical Outrigger or Dimension alongside the base table with '9999-12-31 UTC' sentinels",
                        "refactor_remedy": "Convert the dimension to full SCD2, deprecate natural keys, and backfill historical surrogate keys"
                    })
                    
            # 4. Workload Intent Conflict: Analytical Warehouse on Live OLTP
            current_workload = str(baseline_vectors.get("workload_intent", "OLAP")).upper()
            if any(w in current_workload for w in ["OLTP", "LIVE_APP", "TRANSACTIONAL"]):
                olap_indicators = ["10-year trend", "multi-year analytical", "data warehouse", "billion row", "olap cube", "executive bi", "long-term history"]
                if any(ind in combined for ind in olap_indicators):
                    conflicts.append({
                        "rule": rule.get("description"),
                        "vector_violated": "workload_intent",
                        "current_state": "Live Sub-Second Application (OLTP 3NF)",
                        "rule_demands": "Analytical Warehouse Reporting (OLAP)",
                        "business_risk": "Risk of live production application slowdowns or locking crashes if heavy analytical aggregation runs on operational tables",
                        "additive_remedy": "Decouple into a Medallion Gold Dimensional Mart fed asynchronously via CDC from the OLTP source",
                        "refactor_remedy": "Migrate the database to an OLAP columnar engine (requires refactoring all application write queries)"
                    })
                    
            # 5. Lifecycle Funnel Conflict: Multi-stage tracking on single-event transaction fact
            current_lifecycle = str(baseline_vectors.get("lifecycle_funnel", "SINGLE_EVENT")).upper()
            if any(l in current_lifecycle for l in ["SINGLE_EVENT", "TRANSACTION"]):
                lifecycle_indicators = ["multi-stage turnaround", "stage tracking", "placed to delivered", "lead to closed", "applied to funded", "milestones duration", "turnaround time"]
                if any(ind in combined for ind in lifecycle_indicators):
                    conflicts.append({
                        "rule": rule.get("description"),
                        "vector_violated": "lifecycle_funnel",
                        "current_state": "Single-Event Transaction Fact (1 row per checkout/event)",
                        "rule_demands": "Multi-Stage Accumulating Snapshot Fact",
                        "business_risk": "Risk of data bloat and inability to compute milestone lag durations without massive self-joins",
                        "additive_remedy": "Sprout an Accumulating Snapshot Fact Mart (fact_lifecycle_milestones) with milestone date foreign keys",
                        "refactor_remedy": "Rebuild the transaction fact table into an accumulating milestone model"
                    })

        if not conflicts:
            return None
            
        primary = conflicts[0]
        plain_alert = (
            f"🚨 ARCHITECTURAL CONFLICT DETECTED ON VECTOR: {primary['vector_violated'].upper()}\n\n"
            f"• Conflicting Business Rule: \"{primary['rule']}\"\n"
            f"• Current Model Baseline: {primary['current_state']}\n"
            f"• Rule Requirement: {primary['rule_demands']}\n"
            f"• Specific Business Risk: {primary['business_risk']}\n\n"
            f"Please choose how you would like the model to resolve this conflict:\n"
            f"1. [RECOMMENDED] ADD_COMPANION_MART: Add as an additional requirement on top (Enterprise Bus Pattern).\n"
            f"   Pros: Zero downtime, existing dashboards continue running without disruption.\n"
            f"   Action: {primary['additive_remedy']}.\n\n"
            f"2. FULL_REFACTOR: Refactor the whole model (Destructive Replacement).\n"
            f"   Pros: Unified single model; Cons: Breaks existing downstream dashboards and requires a historical backfill.\n"
            f"   Action: {primary['refactor_remedy']}."
        )
        
        return {
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "primary_conflict": primary,
            "alert": plain_alert,
            "options": [
                {
                    "id": "ADD_COMPANION_MART",
                    "title": "(Recommended) Add as an additional requirement on top (Enterprise Bus Pattern)",
                    "description": primary["additive_remedy"]
                },
                {
                    "id": "FULL_REFACTOR",
                    "title": "Refactor the whole model (Replace existing architecture)",
                    "description": primary["refactor_remedy"]
                }
            ]
        }


class IntakeEngine:
    """
    Master Phase 0 Intake Engine enforcing strict 100% information completeness
    via natural business discovery before allowing downstream data model authoring.
    """
    
    @classmethod
    def process_intake(
        cls, 
        narrative: str, 
        business_answers: Optional[List[str]] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
        baseline_vectors: Optional[Dict[str, Any]] = None,
        architectural_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        # 0. Pre-Flight Vector Conflict Detection (Workflow 2 Guardrail)
        if rules and baseline_vectors:
            conflict_res = VectorConflictDetector.detect_conflicts(rules, baseline_vectors)
            if conflict_res and not architectural_choice:
                return {
                    "status": "AWAITING_ARCHITECTURAL_CONFIRMATION",
                    "completeness_score": 100.0,
                    "conflict_details": conflict_res,
                    "alert": conflict_res["alert"],
                    "options": conflict_res["options"],
                    "message": "Execution halted: A newly submitted business rule conflicts with a baseline vector. User confirmation required."
                }
                
        # 1. Semantic Sanity Check on Base Narrative
        sanity_res = SemanticSanityFilter.validate_narrative(narrative)
        if not sanity_res["valid"]:
            return {
                "status": "REJECTED",
                "rejection_reason": sanity_res["reason"],
                "message": sanity_res["message"],
                "completeness_score": 0.0,
                "questions": []
            }
            
        # 2. Enrich Narrative with Business Answers
        if business_answers:
            enriched_narrative = f"{narrative} {' '.join(business_answers)}"
        else:
            enriched_narrative = narrative
            
        # 3. Parse Entities via DDD Noun-Verb Parser
        parsed_semantics = NounVerbSemanticParser.parse_workflow_narrative(enriched_narrative)
        
        # 4. Score Information Completeness (Strict 100% Gate)
        completeness = IntakeCompletenessScorer.score_completeness(enriched_narrative, parsed_semantics)
        
        # 5. HARD GATE: If Completeness < 100.0%, block spec output and generate targeted natural questions
        if not completeness["is_sufficient"]:
            domain_roles = NounVerbSemanticParser.extract_domain_roles(enriched_narrative, parsed_semantics)
            questions = AdaptiveBusinessInterviewer.get_questions_for_missing_vectors(completeness["missing_vectors"], domain_roles=domain_roles)
            return {
                "status": "NEEDS_CLARIFICATION",
                "completeness_score": completeness["completeness_score"],
                "resolved_vectors": completeness["resolved_vectors"],
                "missing_vectors": completeness["missing_vectors"],
                "parsed_semantics": parsed_semantics,
                "questions": questions,
                "message": f"Intake is {completeness['completeness_score']:.0f}% complete. Please answer the {len(questions)} natural business question(s) to reach 100% certified completeness."
            }
            
        # 6. If Completeness == 100%, Infer Technical Parameters & Classify Architecture
        inferred_params = NounVerbSemanticParser.infer_parameters_from_business_narrative(enriched_narrative)
        arch_decision = DataModelDecisionEngine.classify_architecture(**inferred_params)
        
        return {
            "status": "CERTIFIED_READY",
            "completeness_score": completeness["completeness_score"],
            "resolved_vectors": completeness["resolved_vectors"],
            "missing_vectors": completeness["missing_vectors"],
            "enriched_narrative": enriched_narrative,
            "parsed_semantics": parsed_semantics,
            "inferred_params": inferred_params,
            "architecture_decision": arch_decision,
            "questions": [],
            "message": "Intake certified at 100% completeness via natural business discovery. Ready for Data Model Architect handoff."
        }
