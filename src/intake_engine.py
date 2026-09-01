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
    2. Entity Grain (1 row per item / transaction / snapshot) - 20%
    3. Temporal History Policy (SCD2 historical vs. SCD1 in-place overwrite) - 20%
    4. Lifecycle Funnel (Single standalone event vs. Sequential multi-stage) - 20%
    5. Relationship Multiplicity (1:1, 1:N, M:N bridge) - 20%
    
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
            
        # Vector 2: Entity Grain
        nouns = parsed_entities.get("dimensions_nouns", [])
        grain_keywords = [
            "line item", "order line", "transaction", "each encounter", "single event",
            "snapshot", "one row per", "individual", "prescription", "procedure",
            "order", "patient", "stay", "admission", "vitals"
        ]
        if len(nouns) >= 2 and any(k in text for k in grain_keywords):
            resolved_vectors["entity_grain"] = True
        elif len(nouns) >= 3:
            resolved_vectors["entity_grain"] = True
        else:
            resolved_vectors["entity_grain"] = False
            missing_vectors.append("entity_grain")
            
        # Vector 3: Temporal History Policy
        temporal_keywords = [
            "preserve", "historical", "scd", "original address", "point-in-time",
            "overwrite", "newest address", "audit date", "regulated", "sox",
            "insurance at time", "newest policy", "always overwrite"
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
            "point-of-sale", "sale", "sales", "checkout"
        ]
        if any(k in text for k in lifecycle_keywords):
            resolved_vectors["lifecycle_funnel"] = True
        else:
            resolved_vectors["lifecycle_funnel"] = False
            missing_vectors.append("lifecycle_funnel")
            
        # Vector 5: Relationship Multiplicity
        if len(nouns) >= 2:
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
    Dynamically generates targeted, 100% plain-English multiple-choice questions
    ONLY for the specific missing architectural vectors.
    """
    
    QUESTION_BANK = {
        "workload_intent": {
            "id": "q_workload_intent",
            "question": "How will your team or end-users primarily interact with this system?",
            "options": [
                "(Recommended) We want to build executive dashboards, BI reports, and analyze performance trends over time.",
                "This directly powers a live user-facing website, mobile app, point-of-care EHR, or checkout screen where instant sub-second updates are critical.",
                "We are collecting continuous real-time data streams from sensors, tracking devices, or market tickers every second."
            ]
        },
        "temporal_policy": {
            "id": "q_temporal_policy",
            "question": "When a customer, patient, or profile changes (like moving to a new address or updating insurance), how should historical records look?",
            "options": [
                "(Recommended) Past historical records should preserve the original profile and insurance policy at the time of each event so past billing and audits stay accurate.",
                "Always overwrite past records with their newest address and policy everywhere across the system.",
                "We are legally/financially regulated (SOX, Banking, HIPAA) and need to prove exactly what our accounting/clinical records showed on any past audit date."
            ]
        },
        "lifecycle_funnel": {
            "id": "q_lifecycle_funnel",
            "question": "Does this business process involve multiple sequential steps where you need to track turnaround time?",
            "options": [
                "(Recommended) Yes, we need to track how long it takes to move across stages (e.g. from Order Placed -> Shipped -> Delivered, or Admission -> Bed Assignment -> Discharge).",
                "No, we only need to record each individual event or transaction as a single standalone event.",
                "We need periodic daily or monthly summary snapshots of total balances, inventory stock, or bed occupancy."
            ]
        },
        "entity_grain": {
            "id": "q_entity_grain",
            "question": "What is the primary level of detail (grain) for measuring activity in this business?",
            "options": [
                "(Recommended) Detailed line-item or clinical event level (e.g., individual medications prescribed, individual line items).",
                "Encounter / Order summary level (e.g., total basket or stay summary).",
                "Periodic summary rollup level (e.g., daily total store revenue or hospital bed occupancy)."
            ]
        },
        "relationship_multiplicity": {
            "id": "q_relationship_multiplicity",
            "question": "Are there many-to-many relationships involved in this workflow?",
            "options": [
                "(Recommended) Standard one-to-many relationships (e.g. 1 patient has many stays, 1 customer has many orders).",
                "Complex many-to-many co-ownership (e.g. joint accounts with multiple owners, claims with multiple primary diagnoses)."
            ]
        }
    }
    
    @classmethod
    def get_questions_for_missing_vectors(cls, missing_vectors: List[str]) -> List[Dict[str, Any]]:
        return [cls.QUESTION_BANK[vec] for vec in missing_vectors if vec in cls.QUESTION_BANK]


class IntakeEngine:
    """
    Master Phase 0 Intake Engine enforcing strict 100% information completeness
    before allowing downstream data model authoring or spec output.
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
        
        # 5. HARD GATE: If Completeness < 100.0%, block spec output and generate targeted questions
        if not completeness["is_sufficient"]:
            questions = AdaptiveBusinessInterviewer.get_questions_for_missing_vectors(completeness["missing_vectors"])
            return {
                "status": "NEEDS_CLARIFICATION",
                "completeness_score": completeness["completeness_score"],
                "resolved_vectors": completeness["resolved_vectors"],
                "missing_vectors": completeness["missing_vectors"],
                "parsed_semantics": parsed_semantics,
                "questions": questions,
                "message": f"Intake is {completeness['completeness_score']:.0f}% complete. All 5 architectural vectors must reach 100% before generating data model specs. Please answer the remaining {len(questions)} question(s)."
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
            "message": "Intake certified at 100% completeness. Ready for Data Model Architect handoff."
        }
