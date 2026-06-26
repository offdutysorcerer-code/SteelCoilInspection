$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$PyProject = @'
[project]
name = "steel-coil-inspection"
version = "0.1.0"
description = "Steel coil shipment inspection pipeline: dataset preparation, object detection, coil ID OCR, and rule-based reports."
requires-python = ">=3.11,<3.13"
dependencies = [
    "opencv-python>=4.8.0",
    "ultralytics>=8.3.0",
    "pillow>=10.0.0",
    "pyyaml>=6.0.1",
    "pandas>=2.0.0",
    "paddleocr>=2.7.0",
    "paddlepaddle>=2.6.0",
    "rich>=13.0.0",
    "label-studio>=1.12.0",
]

[project.scripts]
steelcoil = "steelcoil.cli:main"

[tool.uv]
package = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/steelcoil"]
'@

# PowerShell 5.1 的 Set-Content -Encoding UTF8 會寫入 BOM，tomllib 可能在 line 1 column 1 報錯。
# 這裡強制寫成 UTF-8 without BOM。
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $ProjectRoot "pyproject.toml"), $PyProject, $Utf8NoBom)

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv command not found. Please install uv first."
}

uv sync
if ($LASTEXITCODE -ne 0) {
    throw "uv sync failed with exit code $LASTEXITCODE"
}

Write-Host "uv project initialized."
