$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Path = Join-Path $ProjectRoot "pyproject.toml"
if (Test-Path $Path) {
    $Text = Get-Content $Path -Raw -Encoding UTF8
    $Text = $Text -replace '    "label-studio>=1\.12\.0",\r?\n', ''
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom)
    Write-Host "Removed label-studio dependency from pyproject.toml"
}

uv sync
