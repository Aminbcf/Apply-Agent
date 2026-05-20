<#
.SYNOPSIS
Runs the backend unit tests for the Apply-Agent project.
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "src\backend"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Running Backend Unit Tests..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Push-Location $BackendDir

try {
    # Run pytest module
    python -m pytest -c pytest.ini
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "Failed to execute pytest. Is python in your PATH?" -ForegroundColor Red
    $exitCode = 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "All tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed. Check the output above." -ForegroundColor Red
}
Write-Host "==================================================" -ForegroundColor Cyan

exit $exitCode
