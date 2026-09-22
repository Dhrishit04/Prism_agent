param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
}

python -m pip install --upgrade pyinstaller
python -m PyInstaller --clean --noconfirm ..\main.py-x86_64-pc-windows-msvc.spec
Write-Host "Built dist/main.py-x86_64-pc-windows-msvc.exe"
