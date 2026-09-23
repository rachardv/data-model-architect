# 🛠️ Data Model Architect - Forge Automation Runner
# Usage:
#   .\forge.ps1 fast              -> [Recommended] Run fast inner-loop (core unit tests + 14-case regression diff in ~10s)
#   .\forge.ps1 promote           -> Run full 219-check certification, merge staging -> main, and push to origin & synology
#   .\forge.ps1 test [CASE-ID]    -> Run a single case (e.g. .\forge.ps1 test CASE-10)
#   .\forge.ps1 diff              -> Run regression diff against golden snapshot
#   .\forge.ps1 strict-diff       -> Run regression diff and fail on any drift (CI gate)
#   .\forge.ps1 certify           -> Run full Forge industry battery (TPC-H, TPC-DI, SSB, Spider)
#   .\forge.ps1 snapshot          -> Promote current run as the new certified golden baseline
#   .\forge.ps1 tree              -> Regenerate docs/DECISION_TREE.md in <30ms with zero credits
#   .\forge.ps1 tests             -> Run the full 144+ pytest suite
#   .\forge.ps1 all               -> Run tests + diff + forge certification in sequence
#   .\forge.ps1 list              -> Discover and list all declarative benchmark cases
# Flags:
#   -v, -VerboseMode              -> Enable full verbose logging (DATA_MODEL_LOG_LEVEL=INFO)

param (
    [Parameter(Position=0)]
    [ValidateSet("fast", "promote", "test", "diff", "strict-diff", "certify", "snapshot", "tests", "all", "list", "tree")]
    [string]$Command = "fast",

    [Parameter(Position=1)]
    [string]$TargetCase = "",

    [Parameter()]
    [string]$Workload = "",

    [Parameter()]
    [string]$Domain = "",

    [Parameter()]
    [Alias("v")]
    [switch]$VerboseMode
)

$ErrorActionPreference = "Stop"

# 1. Log Suppression / Error Burst Configuration
if ($VerboseMode) {
    $env:DATA_MODEL_LOG_LEVEL = "INFO"
    $env:DATA_MODEL_LOG_JSON = "true"
} else {
    $env:DATA_MODEL_LOG_LEVEL = "WARNING"
}

# 2. Branch Awareness & Active Status Badge
$CurrentBranch = (git branch --show-current 2>$null)
if (-not $CurrentBranch) { $CurrentBranch = "main" }

Write-Host "==================================================" -ForegroundColor DarkGray
if ($CurrentBranch -eq "staging") {
    Write-Host "🌿 [ACTIVE BRANCH: staging] - Fast inner-loop mode recommended" -ForegroundColor Green
} elseif ($CurrentBranch -eq "main") {
    Write-Host "🛡️ [ACTIVE BRANCH: main] - Production release branch (Full certification mandatory)" -ForegroundColor Yellow
} else {
    Write-Host "🌿 [ACTIVE BRANCH: $CurrentBranch]" -ForegroundColor Cyan
}
Write-Host "==================================================" -ForegroundColor DarkGray

# 3. Optional Filter Flags for CLI
$FilterArgs = ""
if ($Workload) { $FilterArgs += " --workload $Workload" }
if ($Domain) { $FilterArgs += " --domain $Domain" }

function Run-PyCommand {
    param(
        [string]$Cmd,
        [string]$Description = ""
    )
    if ($Description) {
        Write-Host "`n>> $Description" -ForegroundColor Cyan
    } else {
        Write-Host "`n>> py -3.14 $Cmd" -ForegroundColor Cyan
    }
    
    Invoke-Expression "py -3.14 $Cmd"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Execution failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

switch ($Command) {
    "list" {
        Run-PyCommand "-m forge.cli --list-cases$FilterArgs"
    }

    "fast" {
        Write-Host "`n==================================================" -ForegroundColor Green
        Write-Host "⚡ EXECUTING FAST FORGE INNER LOOP (~10s)" -ForegroundColor Green
        Write-Host "==================================================" -ForegroundColor Green
        
        Write-Host "`n[Step 1/2] Core Strategy & Schema Generators (0.8s)..." -ForegroundColor Yellow
        Run-PyCommand "-m pytest tests/test_risk_taxonomy_sync.py tests/test_decision_tree_sync.py tests/test_catalog_loader.py tests/test_semantic_benchmarks.py tests/test_vector_conflict_guardrail.py tests/test_dynamic_intake_questions.py tests/test_sttm_generator.py tests/test_dbt_generator.py tests/test_medallion_pipeline.py -q --tb=short"
        
        Write-Host "`n[Step 2/2] Golden Baseline Strict Diff (~9s)..." -ForegroundColor Yellow
        Run-PyCommand "-m forge.cli --benchmark-gate --diff --strict-drift"
        
        Write-Host "`n✨ FAST INNER LOOP PASSED: Zero schema drift or regressions across core engine and benchmark catalog!" -ForegroundColor Green
    }

    "test" {
        if (-not $TargetCase) {
            Write-Host "Please specify a case ID, e.g.: .\forge.ps1 test CASE-10" -ForegroundColor Yellow
            Run-PyCommand "-m forge.cli --list-cases$FilterArgs"
            exit 1
        }
        Run-PyCommand "-m forge.cli --benchmark-case $TargetCase"
    }

    "diff" {
        Run-PyCommand "-m forge.cli --benchmark-gate --diff$FilterArgs"
    }

    "strict-diff" {
        Run-PyCommand "-m forge.cli --benchmark-gate --diff --strict-drift$FilterArgs"
    }

    "certify" {
        Run-PyCommand "-m forge.cli --forge"
    }

    "snapshot" {
        Run-PyCommand "-m forge.cli --benchmark-gate --snapshot"
    }

    "tree" {
        Run-PyCommand "-m forge.decision_tree_generator" "Auto-regenerating docs/DECISION_TREE.md (zero-cost reflection)..."
    }

    "tests" {
        Run-PyCommand "-m pytest -q --tb=short"
    }

    "all" {
        Write-Host "`n==================================================" -ForegroundColor Magenta
        Write-Host "🛠️  EXECUTING FULL FORGE VERIFICATION BATTERY" -ForegroundColor Magenta
        Write-Host "==================================================" -ForegroundColor Magenta
        
        Write-Host "`n[Step 1/3] Pytest Universal Suite (144 tests)..." -ForegroundColor Yellow
        Run-PyCommand "-m pytest -q --tb=short"

        Write-Host "`n[Step 2/3] Golden Snapshot Regression Diff Guard (14 cases)..." -ForegroundColor Yellow
        Run-PyCommand "-m forge.cli --benchmark-gate --diff --strict-drift"

        Write-Host "`n[Step 3/3] Forge Industry Certification Battery (219 checks)..." -ForegroundColor Yellow
        Run-PyCommand "-m forge.cli --forge"

        Write-Host "`n✨ 100% FORGE CERTIFICATION COMPLETE: Zero Regressions Detected!" -ForegroundColor Green
    }

    "promote" {
        Write-Host "`n==================================================" -ForegroundColor Magenta
        Write-Host "🚀 PROMOTING STAGING TO MAIN (Full Certification Gate)" -ForegroundColor Magenta
        Write-Host "==================================================" -ForegroundColor Magenta
        
        $ActiveBranch = (git branch --show-current 2>$null)
        if ($ActiveBranch -ne "staging") {
            Write-Host "`n❌ Error: Promotion must be initiated from the 'staging' branch. Current branch: '$ActiveBranch'" -ForegroundColor Red
            exit 1
        }
        
        # Verify clean working tree
        $gitStatus = git status --porcelain
        if ($gitStatus) {
            Write-Host "`n❌ Error: Working tree has uncommitted changes. Please commit or stash before promoting." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "`n[Step 1/4] Running Full 144-Test Pytest Suite..." -ForegroundColor Yellow
        Run-PyCommand "-m pytest -q --tb=short"
        
        Write-Host "`n[Step 2/4] Verifying 14-Case Golden Baseline Strict Diff..." -ForegroundColor Yellow
        Run-PyCommand "-m forge.cli --benchmark-gate --diff --strict-drift"
        
        Write-Host "`n[Step 3/4] Executing 219-Check Industry Certification Battery..." -ForegroundColor Yellow
        Run-PyCommand "-m forge.cli --forge"
        
        Write-Host "`n[Step 4/4] Merging 'staging' into 'main' and synchronizing remotes..." -ForegroundColor Yellow
        git checkout main
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        
        git merge staging --ff-only
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Fast-forward merge failed. Attempting standard merge..." -ForegroundColor Yellow
            git merge staging -m "chore(release): promote staging to main [certified]"
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        
        Write-Host "`n>> Pushing 'main' to origin..." -ForegroundColor Cyan
        git push origin main
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        
        Write-Host "`n>> Pushing 'main' to synology..." -ForegroundColor Cyan
        git push synology main
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        
        Write-Host "`n>> Returning to 'staging' branch..." -ForegroundColor Cyan
        git checkout staging
        
        Write-Host "`n🎉 PROMOTION SUCCESSFUL: Staging successfully certified and promoted to main on both remotes!" -ForegroundColor Green
    }
}
