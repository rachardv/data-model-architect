import argparse
import sys
import os

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from forge.runner import ForgeEngineRunner
from forge.snapshot_engine import GoldenSnapshotEngine
from forge.predefined_benchmark_gate import PredefinedBenchmarkGate
from forge.benchmark_catalog import get_predefined_benchmark_catalog
from forge.catalog_loader import BenchmarkCatalogLoader
from forge.industry_benchmarks import IndustryBenchmarkRunner
from forge.mega_benchmark import MegaBenchmarkRunner

def main():
    parser = argparse.ArgumentParser(
        description="🛠️ The Forge — Data Model Architect Test Harness & Certification Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py -3.14 -m forge.cli --forge                               Run full Forge certification battery
  py -3.14 -m forge.cli --benchmark-gate --diff               Compare benchmark gate against golden snapshot
  py -3.14 -m forge.cli --benchmark-gate --snapshot           Capture new golden baseline snapshot
  py -3.14 -m forge.cli --list-cases                          List all declarative benchmark cases
  py -3.14 -m forge.cli --benchmark-case CASE-01              Run single benchmark case by ID
  py -3.14 -m forge.cli --industry-benchmark                  Run TPC-DI, TPC-H, SSB, TPC-DS suite
  py -3.14 -m forge.cli --mega-benchmark --cases 10           Run 10 mega-evaluation benchmark cases
        """
    )
    parser.add_argument("--forge", action="store_true", help="Execute 🛠️ Forge Workflow engine certification battery (Predefined Gate + Industry Standards)")
    parser.add_argument("--benchmark-gate", action="store_true", help="Execute Predefined Benchmark Validation Gate 1-by-1 across all cases")
    parser.add_argument("--benchmark-case", type=str, default=None, help="Execute single Predefined Benchmark Case by ID (e.g. CASE-01)")
    parser.add_argument("--catalog-path", type=str, default="benchmarks/catalog", help="Directory path to scan for declarative YAML/JSON benchmark cases (default: benchmarks/catalog)")
    parser.add_argument("--list-cases", action="store_true", help="Discover and list all declarative benchmark cases in the catalog")
    parser.add_argument("--snapshot", action="store_true", help="Capture certified golden baseline snapshot of benchmark gate run")
    parser.add_argument("--diff", action="store_true", help="Compare benchmark gate run against certified golden baseline snapshot")
    parser.add_argument("--strict-drift", action="store_true", help="Fail execution with exit code 1 if schema drift or status deviations are detected")
    parser.add_argument("--baseline-path", type=str, default="benchmarks/baselines/golden_snapshot.json", help="Path to golden baseline snapshot file (default: benchmarks/baselines/golden_snapshot.json)")
    parser.add_argument("--latency-threshold", type=float, default=100.0, help="Query latency regression threshold percentage (default: 100.0%%)")
    parser.add_argument("--industry-benchmark", action="store_true", help="Execute Industry Standards Benchmark Suite (TPC-DI, TPC-H, SSB, TPC-DS, BIRD-SQL, Spider)")
    parser.add_argument("--mega-benchmark", action="store_true", help="Execute Academic & Enterprise Mega-Evaluation Suite")
    parser.add_argument("--cases", type=int, default=25, help="Number of model cases for mega-benchmark (default: 25)")
    parser.add_argument("--fast-nlp", action="store_true", help="Run fast NLP classification instead of full end-to-end model generation for mega-benchmark")
    parser.add_argument("--log-level", type=str, default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Configure log verbosity level (default: from DATA_MODEL_LOG_LEVEL env var or INFO)")

    args = parser.parse_args()
    
    if args.log_level:
        from src.logger import configure_logging
        configure_logging(level=args.log_level.upper())

    # Default action if no arguments provided: print help
    if not any([args.forge, args.benchmark_gate, args.benchmark_case, args.list_cases, 
                args.snapshot, args.diff, args.industry_benchmark, args.mega_benchmark]):
        parser.print_help()
        return

    # 1. Full Forge Certification Battery
    if args.forge:
        sc = ForgeEngineRunner.run_forge_certification()
        ForgeEngineRunner.print_forge_scorecard(sc)
        if sc.get("overall_status") != "PASS":
            sys.exit(1)
        return

    # 2. Industry Standards Benchmark Suite
    if args.industry_benchmark:
        sc = ForgeEngineRunner.run_forge_certification(include_predefined_gate=False)
        ForgeEngineRunner.print_forge_scorecard(sc)
        if sc.get("overall_status") != "PASS":
            sys.exit(1)
        return

    # 3. Discover and List Benchmark Cases
    if args.list_cases:
        BenchmarkCatalogLoader.load_from_directory(args.catalog_path, register=True, clear_existing=True)
        cases = get_predefined_benchmark_catalog()
        print(f"\n=== 📚 PREDEFINED BENCHMARK CATALOG ({len(cases)} cases discovered in '{args.catalog_path}') ===")
        if not cases:
            print("  No benchmark cases found. Add .yaml or .json case definitions to benchmarks/catalog/")
            return
        print(f"{'CASE ID':<10} {'NAME':<34} {'HAZARD CATEGORY':<22} {'TRAP?':<6} {'STATUS':<28}")
        print("-" * 105)
        for c in cases:
            is_trap = "YES" if c.is_intentional_trap else "NO"
            print(f"{c.case_id:<10} {c.name[:32]:<34} {c.hazard_category[:20]:<22} {is_trap:<6} {c.expected_status[:26]:<28}")
            if c.citation:
                print(f"  └─ 📚 Source: {c.citation.strip()}")
        print("-" * 105)
        return

    # 4. Benchmark Gate / Single Case / Snapshot / Diff
    if args.benchmark_gate or args.benchmark_case or args.snapshot or args.diff:
        catalog = get_predefined_benchmark_catalog()
        if not catalog and os.path.exists(args.catalog_path):
            BenchmarkCatalogLoader.load_from_directory(args.catalog_path, register=True)
            catalog = get_predefined_benchmark_catalog()

        gate = PredefinedBenchmarkGate()

        # Single Case Execution
        if args.benchmark_case:
            target_case = next((c for c in catalog if c.case_id.upper() == args.benchmark_case.upper()), None)
            if not target_case:
                print(f"Error: Benchmark case '{args.benchmark_case}' not found in catalog ({len(catalog)} case(s) available).")
                sys.exit(1)
            res = gate.run_case(target_case)
            print(f"\n=== 🎯 PREDEFINED BENCHMARK CASE [{res['case_id']}] ===")
            print(f"Name:          {res['name']}")
            print(f"Domain:        {res['domain']}")
            if target_case.citation:
                print(f"Citation:      {target_case.citation.strip()}")
            print(f"Verdict:       {res['verdict']} in {res['execution_time_ms']}ms")
            print(f"Status:        {res['final_status']} (Expected: {res['expected_status']})")
            print(f"Queries:       {res['queries_passed']}/{res['queries_executed']} passed")
            print(f"Trace JSON:    {res['trace_files']['json_path']}")
            print(f"Trace Report:  {res['trace_files']['md_path']}")
            if res['verdict'] != "PASS":
                sys.exit(1)
            return

        # Run All Cases
        scorecard = gate.run_all_cases()
        print(f"\n=== 🎯 PREDEFINED BENCHMARK GATE SCORECARD ===")
        print(f"Status:            {scorecard['status']} ({scorecard['passed_cases']}/{scorecard['total_cases']} cases passed, {scorecard['pass_rate_pct']}%)")
        print(f"Execution Time:    {scorecard['execution_time_ms']}ms")
        if scorecard['status'] == "EMPTY_CATALOG":
            print(f"Notice:            {scorecard['message']}")
        else:
            print(f"Trap Defenses:     {scorecard['trap_defenses_passed']}/{scorecard['trap_defenses_tested']} verified")
            for c_res in scorecard['cases']:
                badge = "PASS" if c_res['verdict'] == "PASS" else "FAIL"
                print(f"  • [{badge}] {c_res['case_id']}: {c_res['name']} ({c_res['execution_time_ms']}ms)")

        # Handle Golden Snapshot Capture
        if args.snapshot:
            snap = GoldenSnapshotEngine.capture_snapshot(scorecard["cases"], args.baseline_path)
            print(f"\n📸 [SNAPSHOT CAPTURED] Golden baseline saved to: {args.baseline_path} ({len(snap['cases'])} cases)")

        # Handle Regression Diffing
        if args.diff:
            baseline = GoldenSnapshotEngine.load_snapshot(args.baseline_path)
            if not baseline:
                print(f"\n⚠️  Cannot diff: No golden baseline found at '{args.baseline_path}'. Run with --snapshot first.")
                if args.strict_drift:
                    sys.exit(1)
                return
            diff_res = GoldenSnapshotEngine.compare_run_to_snapshot(
                live_results=scorecard["cases"],
                snapshot=baseline,
                latency_threshold_pct=args.latency_threshold
            )
            print(GoldenSnapshotEngine.format_diff_terminal_report(diff_res))
            if args.strict_drift and diff_res["has_drift"]:
                print(f"\n❌ [STRICT DRIFT GATE FAILED] Schema drift or status deviations detected.")
                sys.exit(1)

        if scorecard.get("status") != "PASS":
            sys.exit(1)
        return

    # 5. Mega-Benchmark
    if args.mega_benchmark:
        MegaBenchmarkRunner.run_mega_benchmark(
            total_cases=args.cases,
            verbose=True,
            end_to_end=not args.fast_nlp
        )
        return

if __name__ == "__main__":
    main()
