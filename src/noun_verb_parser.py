from typing import Dict, List, Any

class NounVerbSemanticParser:
    """
    Domain-Driven Design (DDD) parser that decomposes raw business workflow text
    into Dimensions (Nouns), Facts & State Triggers (Verbs), and Statuses (Adjectives).
    """
    
    @staticmethod
    def parse_workflow_narrative(narrative: str) -> Dict[str, List[str]]:
        # Lightweight token heuristic analyzer
        words = [w.strip(".,;:()\"'").lower() for w in narrative.split()]
        
        # Core domain taxonomy seeds
        noun_indicators = {"customer", "employee", "product", "department", "manager", "order", "claim", "patient", "driver", "warehouse", "store", "account"}
        verb_indicators = {"places", "orders", "promotes", "transfers", "pays", "ships", "delivers", "refunds", "charges", "admits", "executes", "buys"}
        adjective_indicators = {"active", "remote", "shipped", "pending", "cancelled", "approved", "high", "low", "returned"}
        
        extracted_nouns = sorted(list({w for w in words if w in noun_indicators or w.endswith("er") or w.endswith("ee") or w.endswith("ment")}))
        extracted_verbs = sorted(list({w for w in words if w in verb_indicators or w.endswith("s") or w.endswith("ed")}))
        extracted_adjectives = sorted(list({w for w in words if w in adjective_indicators or w.endswith("able") or w.endswith("ed")}))
        
        return {
            "dimensions_nouns": extracted_nouns,
            "facts_verbs": extracted_verbs,
            "statuses_adjectives": extracted_adjectives
        }
