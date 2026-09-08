param([switch]$Offline, [switch]$VerifyOnly, [switch]$Build)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
function Get-AssetHash([string]$filePath) {
    $stream = [IO.File]::OpenRead($filePath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
$dependencyManifest = Get-Content -LiteralPath (Join-Path $projectRoot 'dependencies.lock.json') -Raw | ConvertFrom-Json
$pythonAsset = $dependencyManifest.assets | Where-Object { $_.path -like '*embed-arm64.zip' } | Select-Object -First 1
$pythonZip = Join-Path $projectRoot $pythonAsset.path
$pythonExe = Join-Path $projectRoot 'runtime\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    if ($VerifyOnly) { throw 'Private ARM64 runtime is missing. Run setup without VerifyOnly.' }
    $validZip = (Test-Path -LiteralPath $pythonZip) -and ((Get-AssetHash $pythonZip) -eq $pythonAsset.sha256)
    if (-not $validZip) {
        if ($Offline) { throw 'Verified offline Python ZIP is missing.' }
        New-Item -ItemType Directory -Path (Split-Path -Parent $pythonZip) -Force | Out-Null
        $partialZip = $pythonZip + '.partial'
        Invoke-WebRequest -Uri $pythonAsset.url -OutFile $partialZip -UseBasicParsing
        if ((Get-AssetHash $partialZip) -ne $pythonAsset.sha256) { throw 'Python download checksum mismatch.' }
        Move-Item -LiteralPath $partialZip -Destination $pythonZip -Force
    }
    $runtimeDir = Split-Path -Parent $pythonExe
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($pythonZip)
    try {
        foreach ($entry in $archive.Entries) {
            $entryPath = [IO.Path]::GetFullPath((Join-Path $runtimeDir $entry.FullName))
            if (-not $entryPath.StartsWith($runtimeDir + '\')) { throw 'Unsafe Python archive entry.' }
            if ($entry.Name -eq '') { New-Item -ItemType Directory -Path $entryPath -Force | Out-Null }
            else {
                New-Item -ItemType Directory -Path (Split-Path -Parent $entryPath) -Force | Out-Null
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $entryPath, $true)
            }
        }
    } finally { $archive.Dispose() }
    New-Item -ItemType Directory -Path (Join-Path $runtimeDir 'Lib\site-packages') -Force | Out-Null
    @('python311.zip','.','Lib/site-packages','..','import site') | Set-Content -LiteralPath (Join-Path $runtimeDir 'python311._pth') -Encoding ascii
}
& $pythonExe -c "import platform; assert platform.machine().upper()=='ARM64', 'Native ARM64 runtime required'"
if ($LASTEXITCODE -ne 0) { throw 'Runtime architecture check failed.' }
$setupArgs = @()
if ($Offline) { $setupArgs += '--offline' }
if ($VerifyOnly) { $setupArgs += '--verify' }
& $pythonExe (Join-Path $PSScriptRoot 'setup_assets.py') --dependencies @setupArgs
if ($LASTEXITCODE -ne 0) { throw 'Dependency asset verification failed.' }
if (-not $VerifyOnly) {
    $pipWheel = Get-ChildItem -LiteralPath (Join-Path $projectRoot 'offline_dependencies\wheels') -Filter 'pip-*.whl' | Select-Object -First 1
    & $pythonExe -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $pipWheel.FullName (Join-Path $projectRoot 'runtime\Lib\site-packages')
    if ($LASTEXITCODE -ne 0) { throw 'Pip bootstrap failed.' }
    & $pythonExe -m pip install --no-index --find-links (Join-Path $projectRoot 'offline_dependencies\wheels') -r (Join-Path $projectRoot 'requirements-lock.txt') --no-user --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed.' }
}
& $pythonExe (Join-Path $PSScriptRoot 'setup_assets.py') @setupArgs
if ($LASTEXITCODE -ne 0) { throw 'Model verification or repair failed.' }
& $pythonExe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
if ($Build) { & (Join-Path $PSScriptRoot 'build.ps1') }
Write-Output 'LectureLive setup and verification completed.'
