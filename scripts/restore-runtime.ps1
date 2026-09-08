$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$modelRoot = Join-Path $projectRoot 'models'
$bundleModels = Join-Path $projectRoot 'dist\LectureLive\_internal\models'
if (-not (Test-Path -LiteralPath $modelRoot) -and (Test-Path -LiteralPath $bundleModels)) {
    Copy-Item -LiteralPath $bundleModels -Destination $modelRoot -Recurse
}
& (Join-Path $PSScriptRoot 'setup.ps1') -Offline
Write-Output 'Offline ARM64 development runtime restored. Normal users can launch the bundled EXE directly.'
