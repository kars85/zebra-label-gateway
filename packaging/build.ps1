# Build the Windows desktop installer end-to-end:
#   frontend (Vite) -> frozen app (PyInstaller) -> installer (NSIS)
#
# Usage (from the repo root):
#   pwsh packaging\build.ps1                 # makensis must be on PATH
#   pwsh packaging\build.ps1 -Makensis "C:\path\to\makensis.exe"
#
# Requires: Node/npm, the Python env with the [web] and [desktop] extras, NSIS.
param(
  [string]$Makensis = "makensis"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Building frontend" -ForegroundColor Cyan
Push-Location web
npm ci
npm run build
Pop-Location

Write-Host "==> Freezing app (PyInstaller)" -ForegroundColor Cyan
python -m PyInstaller packaging\desktop.spec --noconfirm `
  --distpath packaging\dist --workpath packaging\build

Write-Host "==> Building installer (NSIS)" -ForegroundColor Cyan
& $Makensis packaging\installer.nsi

$setup = Join-Path $root "packaging\ZebraLabelGateway-Setup.exe"
if (Test-Path $setup) {
  $size = "{0:N1} MB" -f ((Get-Item $setup).Length / 1MB)
  Write-Host "==> Done: $setup ($size)" -ForegroundColor Green
} else {
  throw "Installer was not produced."
}
