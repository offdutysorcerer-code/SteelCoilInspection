$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path "pyproject.toml")) {
    Write-Host "pyproject.toml not found. Creating it with bootstrap_uv_project.ps1..."
    .\bootstrap_uv_project.ps1
} else {
    uv sync
}

uv run steelcoil init-dirs
uv run steelcoil scan-cases --raw data\raw --out reports
uv run steelcoil prepare --raw data\raw --out data\labeling\images
uv run steelcoil yolo-yaml --labels configs\labels.yaml --out data\yolo_dataset\steel_coil.yaml --dataset-root data\yolo_dataset
uv run steelcoil mock-report --raw data\raw --out reports
