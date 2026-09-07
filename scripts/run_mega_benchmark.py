#!/usr/bin/env python
"""
Standalone Runner for Option C: Academic & Enterprise Mega-Evaluation Suite.
Usage:
    python scripts/run_mega_benchmark.py
    python scripts/run_mega_benchmark.py --cases 500
    python scripts/run_mega_benchmark.py --cases 1000 --export-json docs/mega_benchmark_results.json
"""
import sys
import os
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mega_benchmark import MegaBenchmarkRunner

def main():
    parser = argparse.ArgumentParser(description="Option C: Academic & Enterprise Mega-Evaluation Runner")
    parser.add_argument("--cases", type=int, default=25, help="Total model cases to evaluate (default: 25)")
    parser.add_argument("--fast-nlp", action="store_true", help="Run fast NLP classification instead of full end-to-end model generation")
    parser.add_argument("--export-json", type=str, default=None, help="File path to export full JSON benchmark scorecard")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose live progress output")
    
    args = parser.parse_args()
    report = MegaBenchmarkRunner.run_mega_benchmark(
        total_cases=args.cases,
        export_path=args.export_json,
        verbose=not args.quiet,
        end_to_end=not args.fast_nlp
    )
    
    sys.exit(0 if report["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
