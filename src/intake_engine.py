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
            "sub-second", "live app", "point-of-care"
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
            "patient care", "credit lending", "revenue"
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
    Translates technical architecture gaps into 100% natural, human-friendly business questions.
    """
    
    QUESTION_BANK = {
        "workload_intent": {
            "id": "q_workload_intent",
            "question": "How will your team or end-users primarily interact with this system?",
            "options": [
                "(Recommended) We want to build executive dashboards, BI reports, and analyze business trends over time.",
                "This directly powers a live customer-facing app, website, point-of-care EHR, or checkout screen where instant sub-second updates are critical.",
                "We are collecting continuous real-time data streams from sensors, tracking devices, or market tickers every second."
            ]
        },
        "entity_grain": {
            "id": "q_entity_grain",
            "question": "What does your company primarily sell or provide, and what is the primary activity you want to measure?",
            "options": [
                "(Recommended) Detailed product sales & shopping cart line items (e.g. customers buying physical or digital goods).",
                "Recurring subscription memberships & monthly billing renewals (e.g. SaaS software, gym memberships, subscriptions).",
                "Healthcare & clinical patient care (e.g. hospital admissions, doctor visits, medication prescriptions).",
                "Financial lending & banking accounts (e.g. commercial business loans, deposits, mortgage applications)."
            ]
        },
        "temporal_policy": {
            "id": "q_temporal_policy",
            "question": "When a customer, store, or patient updates their profile (like moving to a new address), how should historical reports behave?",
            "options": [
                "(Recommended) Historical reports should preserve their original address and profile at the exact time of each event so past regional sales remain accurate (SCD Type 2).",
                "Always overwrite past records with their newest address and profile everywhere across the system (SCD Type 1).",
                "We are strictly regulated (SOX, Banking, HIPAA) and need to prove exactly what our accounting/clinical records showed on any historical audit date."
            ]
        },
        "lifecycle_funnel": {
            "id": "q_lifecycle_funnel",
            "question": "Does this business workflow involve tracking turnaround time across multiple sequential stages?",
            "options": [
                "(Recommended) Yes, multi-stage turnaround tracking (e.g. from Order Placed -> Picked -> Shipped -> Delivered, or Loan Applied -> Approved -> Funded).",
                "No, single standalone transaction events (e.g. discrete store sales, point-of-sale receipt scans).",
                "Periodic state summary rollups (e.g. monthly balance snapshots, daily warehouse inventory counts)."
            ]
        },
        "relationship_multiplicity": {
            "id": "q_relationship_multiplicity",
            "question": "In your day-to-day operations, do multiple people share accounts, or can an order/case involve multiple primary owners?",
            "options": [
                "(Recommended) Standard one-to-one ownership (e.g. 1 customer per order, 1 primary owner per account).",
                "Shared co-ownership (e.g. joint bank accounts with multiple co-signers, patient cases with multiple attending doctors)."
            ]
        }
    }
    
    @classmethod
    def get_questions_for_missing_vectors(cls, missing_vectors: List[str]) -> List[Dict[str, Any]]:
        return [cls.QUESTION_BANK[vec] for vec in missing_vectors if vec in cls.QUESTION_BANK]


class IntakeEngine:
    """
    Master Phase 0 Intake Engine enforcing strict 100% information completeness
    via natural business discovery before allowing downstream data model authoring.
    """
    
    @classmethod
    def process_intake(cls, narrative: str, business_answers: Optional[List[str]] = None) -> Dict[str, Any]:
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
            questions = AdaptiveBusinessInterviewer.get_questions_for_missing_vectors(completeness["missing_vectors"])
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
