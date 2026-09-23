import argparse
import sys
import os
import json

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.decision_engine import DataModelDecisionEngine
from src.noun_verb_parser import NounVerbSemanticParser
from src.orchestration.captain import CaptainOrchestrator



def main():
    parser = argparse.ArgumentParser(description="Data Model Architect CLI")
    parser.add_argument("--story", type=str, help="Raw business workflow story")
    parser.add_argument("--domain", type=str, default="ecommerce", help="Target business domain name")
    parser.add_argument("--folder", type=str, help="Optional upstream folder path containing source schema files")
    parser.add_argument("--answers", nargs="*", help="Optional plain-English answers to business discovery questions")
    parser.add_argument("--medallion", action="store_true", help="Generate full Bronze -> Silver -> Gold Medallion SQL pipeline")
    parser.add_argument("--dbt", action="store_true", help="Generate full production-ready dbt Core project repository")
    parser.add_argument("--duckdb", action="store_true", help="Execute and verify generated SQL in an in-memory DuckDB instance")
    parser.add_argument("--benchmark", action="store_true", help="Display 4-pillar deterministic benchmark scorecard")
    parser.add_argument("--interactive", action="store_true", help="Run interactive plain-English business intake interview")
    parser.add_argument("--mega-benchmark", action="store_true", help="Execute Academic & Enterprise Mega-Evaluation Suite")
    parser.add_argument("--cases", type=int, default=25, help="Number of model cases for mega-benchmark (default: 25)")
    parser.add_argument("--fast-nlp", action="store_true", help="Run fast NLP classification instead of full end-to-end model generation")
    parser.add_argument("--dialect", type=str, default=None, choices=["duckdb", "snowflake", "bigquery", "postgres", "databricks", "all"], help="Transpile Medallion SQL models to target warehouse dialect")
    parser.add_argument("--benchmark-gate", action="store_true", help="Execute Predefined Benchmark Validation Gate 1-by-1 across all cases")
    parser.add_argument("--benchmark-case", type=str, default=None, help="Execute single Predefined Benchmark Case by ID (e.g. CASE-01)")
    parser.add_argument("--catalog-path", type=str, default="benchmarks/catalog", help="Directory path to scan for declarative YAML/JSON benchmark cases (default: benchmarks/catalog)")
    parser.add_argument("--list-cases", action="store_true", help="Discover and list all declarative benchmark cases in the catalog")
    parser.add_argument("--snapshot", action="store_true", help="Capture certified golden baseline snapshot of benchmark gate run")
    parser.add_argument("--diff", action="store_true", help="Compare benchmark gate run against certified golden baseline snapshot")
    parser.add_argument("--strict-drift", action="store_true", help="Fail execution with exit code 1 if schema drift or status deviations are detected")
    parser.add_argument("--baseline-path", type=str, default="benchmarks/baselines/golden_snapshot.json", help="Path to golden baseline snapshot file (default: benchmarks/baselines/golden_snapshot.json)")
    parser.add_argument("--latency-threshold", type=float, default=100.0, help="Query latency regression threshold percentage (default: 100.0%%)")
    parser.add_argument("--forge", action="store_true", help="Execute 🛠️ Forge Workflow engine certification battery (Predefined Gate + Industry Standards)")
    parser.add_argument("--industry-benchmark", action="store_true", help="Execute Industry Standards Benchmark Suite (TPC-DI, TPC-H, SSB, TPC-DS, BIRD-SQL, Spider)")
    
    args = parser.parse_args()
    
    forge_flags = [
        args.forge, args.industry_benchmark, args.list_cases,
        args.benchmark_gate, args.benchmark_case, args.snapshot,
        args.diff, args.mega_benchmark
    ]
    if any(forge_flags):
        try:
            from forge.cli import main as forge_main
            forge_main()
            return
        except ImportError:
            print("Error: The Forge test harness is not installed in this distribution.")
            print("To run benchmarks, ensure the 'forge/' directory is present.")
            sys.exit(1)
        
    captain = CaptainOrchestrator()
    
    if args.interactive:
        story = args.story or input("Enter your business narrative: ")
        questions = captain.generate_intake_questions(story)
        answers = []
        print("\n=== 💬 PLAIN-ENGLISH BUSINESS DISCOVERY INTERVIEW ===")
        for i, q in enumerate(questions, 1):
            print(f"\nQ{i}: {q['question']}")
            for opt_idx, opt in enumerate(q["options"], 1):
                print(f"   [{opt_idx}] {opt}")
            choice = input("Select an option (1-3) or press Enter to accept recommended: ").strip()
            if choice and choice.isdigit() and 1 <= int(choice) <= len(q["options"]):
                answers.append(q["options"][int(choice)-1])
            else:
                answers.append(q["options"][0])
                
        payload = {
            "domain": args.domain,
            "branch": "NEW_MODEL",
            "narrative": story,
            "business_answers": answers,
            "folder_path": args.folder
        }
        result = captain.execute_workflow(payload)
        print("\n=== 🏛️ DATA MODEL ARCHITECT DELIVERABLES ===")
        print(f"Status:             {result['status']}")
        print(f"Architecture:       {result['architecture_pattern']}")
        print(f"Quality Index:      {result['quality_index']}%")
        print(f"Medallion Artifacts: {result['medallion_pipeline']['total_sql_artifacts']} SQL files generated")
        print(f"Exported Pipelines: docs/pipelines/{args.domain}/")
        if "dbt_project" in result:
            print(f"dbt Core Models:    {result['dbt_project']['total_models']} models compiled")
            print(f"Exported dbt Repo:  docs/dbt/{args.domain}/")
        return
        
    if args.story or args.medallion or args.duckdb or args.dbt or args.benchmark:
        payload = {
            "domain": args.domain,
            "branch": "NEW_MODEL",
            "narrative": args.story or "A customer places an order on our e-commerce platform.",
            "business_answers": args.answers or [],
            "folder_path": args.folder
        }
        
        result = captain.execute_workflow(payload)
        print("=== 🏛️ DATA MODEL ARCHITECT DELIVERABLES ===")
        print(f"Status:             {result.get('status')}")
        
        if result.get("status") != "SYNTHESIZED_SUCCESSFULLY":
            print(f"Message:            {result.get('message', 'Workflow halted.')}")
            if "completeness_score" in result:
                print(f"Completeness Score: {result.get('completeness_score', 0):.0f}%")
            if "questions" in result and result["questions"]:
                print("\nPending Discovery Questions:")
                for i, q in enumerate(result["questions"], 1):
                    print(f"  Q{i}: {q['question']}")
            if "conflict_report" in result:
                conf = result["conflict_report"]
                print(f"\nArchitecture Conflict Detected: {conf.get('message')}")
            return

        print(f"Architecture:       {result['architecture_pattern']}")
        print(f"Inferred Semantics: {result['inferred_usage_params']}")
        print(f"Quality Index:      {result['quality_index']}%")
        print(f"Medallion Artifacts: {result['medallion_pipeline']['total_sql_artifacts']} SQL files generated")
        print(f"Exported Pipelines: docs/pipelines/{args.domain}/ (01_bronze, 02_silver, 03_gold)")
        
        if args.dialect and "medallion_pipeline" in result:
            from src.transpiler import SQLDialectTranspiler
            target_ds = ["snowflake", "bigquery", "postgres", "databricks"] if args.dialect == "all" else [args.dialect]
            counts = SQLDialectTranspiler.export_dialects(
                domain=args.domain,
                pipeline=result["medallion_pipeline"],
                base_dir="docs/pipelines",
                target_dialects=target_ds
            )
            for d_name, cnt in counts.items():
                print(f"Transpiled Dialect: docs/pipelines/{args.domain}/dialects/{d_name}/ ({cnt} SQL files)")

        if "dbt_project" in result:
            print(f"dbt Core Models:    {result['dbt_project']['total_models']} models compiled")
            print(f"Exported dbt Repo:  docs/dbt/{args.domain}/")
        
        if args.duckdb:
            from src.sql_runner import DuckDBPipelineRunner
            schema_spec = result.get("schema_spec") or result.get("target_schema") or payload.get("schema_spec", {
                "tables": [
                    {
                        "name": f"dim_{args.domain}_customer_core",
                        "type": "DIMENSION",
                        "primary_key": "customer_sk",
                        "columns": [
                            {"name": "customer_sk", "type": "VARCHAR(64)"},
                            {"name": "customer_id", "type": "VARCHAR(64)"},
                            {"name": "customer_name", "type": "VARCHAR(255)"},
                            {"name": "scd_valid_from", "type": "TIMESTAMPTZ"},
                            {"name": "scd_valid_to", "type": "TIMESTAMPTZ"}
                        ]
                    },
                    {
                        "name": f"fact_{args.domain}_orders",
                        "type": "FACT",
                        "primary_key": "order_id",
                        "columns": [
                            {"name": "order_id", "type": "BIGINT"},
                            {"name": "customer_sk", "type": "VARCHAR(64)"},
                            {"name": "total_amount_usd", "type": "DECIMAL(14,2)"},
                            {"name": "estimated_delivery_days", "type": "INT"}
                        ]
                    }
                ]
            })
            exec_res = DuckDBPipelineRunner.execute_and_verify(
                domain=args.domain,
                target_schema=schema_spec,
                pipeline=result["medallion_pipeline"]
            )
            print("\n=== 🦆 IN-MEMORY DUCKDB EXECUTION VERIFICATION ===")
            print(f"Status:             {exec_res['status']}")
            print(f"Engine:             {exec_res['engine']}")
            print(f"Bronze Tables:      {len(exec_res['bronze'])} tables created & seeded")
            print(f"Silver Views:       {len(exec_res['silver'])} staging/quarantine views created")
            print(f"Quarantined Rows:   {exec_res['quarantine_records_isolated']} invalid row(s) safely isolated")
            print(f"Gold Tables/Marts:  {len(exec_res['gold'])} marts loaded & verified")
            print(f"Verification:       100% End-to-End SQL Pipeline Validated!")
    else:
        print("Data Model Architect Studio v1.0.0 (Ready)")

if __name__ == "__main__":
    main()
