$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot 'runtime'
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
Expand-Archive -LiteralPath (Join-Path $projectRoot 'offline_dependencies\python-3.11.9-embed-arm64.zip') -DestinationPath $runtimeDir -Force
$siteDir = Join-Path $runtimeDir 'Lib\site-packages'
New-Item -ItemType Directory -Path $siteDir -Force | Out-Null
@('python311.zip','.','Lib/site-packages','..','import site') | Set-Content -LiteralPath (Join-Path $runtimeDir 'python311._pth') -Encoding ascii
$pipWheel = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'offline_dependencies\wheels') -Filter 'pip-*.whl' | Select-Object -First 1
if (-not $pipWheel) { throw 'Offline pip wheel missing.' }
& (Join-Path $runtimeDir 'python.exe') -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $pipWheel.FullName $siteDir
if ($LASTEXITCODE -ne 0) { throw 'Offline pip bootstrap failed.' }
& (Join-Path $runtimeDir 'python.exe') -m pip install --no-index --find-links (Join-Path $projectRoot 'offline_dependencies\wheels') -r (Join-Path $projectRoot 'requirements-lock.txt') --no-user --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw 'Offline dependency restoration failed.' }
$modelRoot = Join-Path $projectRoot 'models'
if (-not (Test-Path -LiteralPath $modelRoot)) {
    Copy-Item -LiteralPath (Join-Path $projectRoot 'dist\LectureLive\_internal\models') -Destination $modelRoot -Recurse
}
Write-Output 'Offline ARM64 development runtime restored. Normal users can simply launch the bundled EXE.'
