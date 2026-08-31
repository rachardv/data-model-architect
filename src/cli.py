import argparse
import sys
from src.decision_engine import DataModelDecisionEngine
from src.noun_verb_parser import NounVerbSemanticParser

def main():
    parser = argparse.ArgumentParser(description="Data Model Architect CLI")
    parser.add_argument("--story", type=str, help="Raw business workflow story")
    parser.add_argument("--bench", action="store_true", help="Run 10-scenario ground-truth evaluation benchmark")
    
    args = parser.parse_args()
    
    if args.story:
        parsed = NounVerbSemanticParser.parse_workflow_narrative(args.story)
        print("=== EXTRACTED DOMAIN TAXONOMY ===")
        print(f"Dimensions (Nouns): {parsed['dimensions_nouns']}")
        print(f"Facts (Verbs):       {parsed['facts_verbs']}")
        print(f"Statuses (Adjectives): {parsed['statuses_adjectives']}")
    else:
        print("Data Model Architect Engine v1.0.0 (Ready)")

if __name__ == "__main__":
    main()
