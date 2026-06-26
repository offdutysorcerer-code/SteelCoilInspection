$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path "pyproject.toml")) {
    .\bootstrap_uv_project.ps1
}

uv sync

uv run python -m steelcoil.label_studio_tasks --raw data\raw --out data\label_studio_tasks.json

$env:LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED = "true"
$env:LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT = "D:\AIProjects\A1\SteelCoilInspection\data\raw"

Write-Host "Label Studio: http://localhost:8080"
Write-Host "Local Files Root: $env:LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT"
Write-Host "Import JSON: D:\AIProjects\A1\SteelCoilInspection\data\label_studio_tasks.json"
Write-Host "Template: D:\AIProjects\A1\SteelCoilInspection\configs\label_studio_config.txt"

uv run label-studio start --port 8080
