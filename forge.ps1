# 🛠️ Data Model Architect - Forge Automation Runner
# Usage:
#   .\forge.ps1 test [CASE-ID]   -> Run a single case (e.g. .\forge.ps1 test CASE-01)
#   .\forge.ps1 diff              -> Run regression diff against golden snapshot
#   .\forge.ps1 strict-diff       -> Run regression diff and fail on any drift (CI gate)
#   .\forge.ps1 certify           -> Run full Forge industry battery (TPC-H, TPC-DI, SSB, Spider)
#   .\forge.ps1 snapshot          -> Promote current run as the new certified golden baseline
#   .\forge.ps1 tests             -> Run the full 134+ pytest suite
#   .\forge.ps1 all               -> Run tests + diff + forge certification in sequence

param (
    [Parameter(Position=0)]
    [ValidateSet("test", "diff", "strict-diff", "certify", "snapshot", "tests", "all", "list")]
    [string]$Command = "all",

    [Parameter(Position=1)]
    [string]$TargetCase = ""
)

$ErrorActionPreference = "Stop"

function Run-PyCommand {
    param([string]$Cmd)
    Write-Host "`n>> py -3.14 $Cmd" -ForegroundColor Cyan
    Invoke-Expression "py -3.14 $Cmd"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n❌ Execution failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

switch ($Command) {
    "list" {
        Run-PyCommand "src/cli.py --list-cases"
    }
    "test" {
        if (-not $TargetCase) {
            Write-Host "Please specify a case ID, e.g.: .\forge.ps1 test CASE-01" -ForegroundColor Yellow
            Run-PyCommand "src/cli.py --list-cases"
            exit 1
        }
        Run-PyCommand "src/cli.py --benchmark-case $TargetCase"
    }
    "diff" {
        Run-PyCommand "src/cli.py --diff"
    }
    "strict-diff" {
        Run-PyCommand "src/cli.py --diff --strict-drift"
    }
    "certify" {
        Run-PyCommand "src/cli.py --forge"
    }
    "snapshot" {
        Run-PyCommand "src/cli.py --benchmark-gate --snapshot"
    }
    "tests" {
        Run-PyCommand "-m pytest -q"
    }
    "all" {
        Write-Host "`n==================================================" -ForegroundColor Magenta
        Write-Host "🛠️  EXECUTING FULL FORGE VERIFICATION BATTERY" -ForegroundColor Magenta
        Write-Host "==================================================" -ForegroundColor Magenta
        
        Write-Host "`n[Step 1/3] Pytest Universal Suite..." -ForegroundColor Yellow
        Run-PyCommand "-m pytest -q"

        Write-Host "`n[Step 2/3] Golden Snapshot Regression Diff Guard..." -ForegroundColor Yellow
        Run-PyCommand "src/cli.py --diff --strict-drift"

        Write-Host "`n[Step 3/3] Forge Industry Certification Battery..." -ForegroundColor Yellow
        Run-PyCommand "src/cli.py --forge"

        Write-Host "`n✨ 100% FORGE CERTIFICATION COMPLETE: Zero Regressions Detected!" -ForegroundColor Green
    }
}
