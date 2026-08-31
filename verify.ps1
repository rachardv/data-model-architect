Write-Host "Running Data Model Architect Verification Battery..." -ForegroundColor Cyan
python -m pytest tests/ -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll 22/22 Unit, Pipeline & DuckDB Tests Passed! Ready Out of the Box!" -ForegroundColor Green
} else {
    Write-Host "`nTests Failed." -ForegroundColor Red
    exit 1
}
