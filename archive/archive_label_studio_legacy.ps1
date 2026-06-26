$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$ArchiveRoot = Join-Path $ProjectRoot "archive\label_studio_legacy"
$ArchiveScripts = Join-Path $ArchiveRoot "scripts"
$ArchiveConfigs = Join-Path $ArchiveRoot "configs"
$ArchiveDocs = Join-Path $ArchiveRoot "docs"
$ArchiveData = Join-Path $ArchiveRoot "data"

New-Item -ItemType Directory -Force -Path $ArchiveRoot, $ArchiveScripts, $ArchiveConfigs, $ArchiveDocs, $ArchiveData | Out-Null

function Move-IfExists($Source, $DestinationFolder) {
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path $DestinationFolder | Out-Null
        Move-Item -Force -Path $Source -Destination $DestinationFolder
        Write-Host "Archived: $Source"
    }
}

function Copy-IfExists($Source, $DestinationFolder) {
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path $DestinationFolder | Out-Null
        Copy-Item -Force -Path $Source -Destination $DestinationFolder
        Write-Host "Copied reference: $Source"
    }
}

Move-IfExists "run_label_studio.ps1" $ArchiveScripts
Move-IfExists "run_image_server.bat" $ArchiveScripts
Move-IfExists "make_label_tasks.ps1" $ArchiveScripts
Move-IfExists "src\steelcoil\label_studio_tasks.py" $ArchiveScripts
Move-IfExists "data\label_studio_tasks.json" $ArchiveData
Move-IfExists "data\labeling" $ArchiveData

Copy-IfExists "configs\label_studio_config.txt" $ArchiveConfigs
Copy-IfExists "docs\label_studio_guide.md" $ArchiveDocs
Copy-IfExists "docs\label_studio_reimport_fix.md" $ArchiveDocs

Write-Host "Label Studio legacy files archived to: $ArchiveRoot"
Write-Host "Current main flow: .\run_case_labeler.ps1"
