$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; docker compose up --build"
Write-Host "Docker stack launch requested."
