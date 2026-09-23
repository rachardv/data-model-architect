#!/usr/bin/env python3
"""
Git Pre-Commit Hook: Anti-Bloat Documentation Enforcement Gate

Ensures that whenever The Forge components or benchmark catalogs are modified,
the developer has documented the hazard/risk in docs/RISK_TAXONOMY.md and that
tests/test_risk_taxonomy_sync.py passes with 0 drift.
"""

import subprocess
import sys
from pathlib import Path

# Safe utf-8 handling across Windows cp1252 and Linux terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_command(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    return res.returncode, res.stdout + res.stderr


def main():
    # 1. Inspect staged files
    code, output = run_command(["git", "diff", "--cached", "--name-only"])
    if code != 0:
        print(f"[ERROR] Failed to get git staged diff: {output}")
        sys.exit(1)

    staged_files = [line.strip() for line in output.splitlines() if line.strip()]
    
    forge_modified = any(
        f.startswith("forge/") or 
        f.startswith("benchmarks/catalog/curated/")
        for f in staged_files
    )

    if forge_modified:
        docs_staged = "docs/RISK_TAXONOMY.md" in staged_files
        if not docs_staged:
            print("\n" + "=" * 70)
            print("[ABORT] COMMIT REJECTED BY ANTI-BLOAT PROTOCOL")
            print("=" * 70)
            print("You have staged changes in The Forge test harness or catalog:")
            for f in staged_files:
                if f.startswith("forge/") or f.startswith("benchmarks/catalog/curated/"):
                    print(f"  * {f}")
            print("\nHowever, `docs/RISK_TAXONOMY.md` is NOT staged in this commit!")
            print("To prevent unmonitored test bloat, every new risk, rule, battery, or")
            print("benchmark case must be registered in the Master Risk Registry Table.")
            print("\nAction required:")
            print("  1. Update `docs/RISK_TAXONOMY.md` with your new additions.")
            print("  2. Stage the documentation: git add docs/RISK_TAXONOMY.md")
            print("  3. Re-run git commit.")
            print("=" * 70 + "\n")
            sys.exit(1)

    # 2. Check if decision engine or parser modified -> Auto-regenerate docs/DECISION_TREE.md
    engine_modified = any(
        f in ("src/decision_engine.py", "src/noun_verb_parser.py", "src/intake_engine.py")
        for f in staged_files
    )

    if engine_modified:
        print("[SYNC] Decision Engine modified. Auto-regenerating docs/DECISION_TREE.md...")
        gen_code, gen_out = run_command([sys.executable, "-m", "forge.decision_tree_generator"])
        if gen_code != 0:
            print(f"[ERROR] Decision tree generation failed:\n{gen_out}")
            sys.exit(1)
        # Stage regenerated decision tree documentation
        run_command(["git", "add", "docs/DECISION_TREE.md"])
        print("[SYNC] docs/DECISION_TREE.md synchronized and staged.")

    # 3. Run the deterministic taxonomy sync test & decision tree sync test
    print("[CHECK] Running Anti-Bloat Documentation Synchronization Gate...")
    code, test_out = run_command([
        sys.executable, "-m", "pytest",
        "tests/test_risk_taxonomy_sync.py",
        "tests/test_decision_tree_sync.py",
        "-q"
    ])
    if code != 0:
        print("\n" + "=" * 70)
        print("[ABORT] COMMIT REJECTED: DOCUMENTATION SYNC TEST FAILED")
        print("=" * 70)
        print(test_out)
        print("=" * 70 + "\n")
        sys.exit(1)

    print("[PASS] Anti-Bloat Documentation & Decision Tree Gates Passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
