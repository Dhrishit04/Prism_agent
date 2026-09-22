param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
}

& $python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Failed to install PyInstaller" }

& $python -m PyInstaller --clean --noconfirm pyinstaller.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$artifact = Join-Path $PSScriptRoot "dist\tesseract-sidecar-x86_64-pc-windows-msvc.exe"
if (-not (Test-Path $artifact)) { throw "Expected sidecar artifact was not created: $artifact" }
Write-Host "Built $artifact"
