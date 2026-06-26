$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
uv sync
uv run python -m steelcoil.label_studio_tasks --raw data\raw --out data\label_studio_tasks.json --url-base "http://127.0.0.1:8090"
Write-Host "Generated data label_studio_tasks json"
