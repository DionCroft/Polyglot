param([switch]$Offline, [switch]$VerifyOnly, [switch]$Build, [ValidateSet("auto","ARM64","x64")][string]$Architecture = "auto")
. (Join-Path $PSScriptRoot "platform.ps1")
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
function Get-AssetHash([string]$filePath) {
    $stream = [IO.File]::OpenRead($filePath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
$dependencyManifest = Get-Content -LiteralPath (Join-Path $projectRoot $dependencyName) -Raw | ConvertFrom-Json
$pythonAsset = $dependencyManifest.assets | Where-Object { $_.path -like $pythonArchive } | Select-Object -First 1
$pythonZip = Join-Path $projectRoot $pythonAsset.path
$pythonExe = Join-Path $projectRoot ($runtimeName + '\python.exe')
if (-not (Test-Path -LiteralPath $pythonExe)) {
    if ($VerifyOnly) { throw 'Private runtime is missing. Run setup without VerifyOnly.' }
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
    @('python311.zip','.','Lib/site-packages','..') | Set-Content -LiteralPath (Join-Path $runtimeDir 'python311._pth') -Encoding ascii
}
& $pythonExe -s -c "import platform,sys; expected='AMD64' if sys.argv[1]=='x64' else 'ARM64'; assert platform.machine().upper()==expected, 'Runtime architecture mismatch'" $Architecture
if ($LASTEXITCODE -ne 0) { throw 'Runtime architecture check failed.' }
$setupArgs = @('--architecture', $Architecture)
if ($Offline) { $setupArgs += '--offline' }
if ($VerifyOnly) { $setupArgs += '--verify' }
& $pythonExe -s (Join-Path $PSScriptRoot 'setup_assets.py') --dependencies @setupArgs
if ($LASTEXITCODE -ne 0) { throw 'Dependency asset verification failed.' }
if (-not $VerifyOnly) {
    $pipWheel = Get-ChildItem -LiteralPath (Join-Path $projectRoot $wheelsName) -Filter 'pip-*.whl' | Select-Object -First 1
    & $pythonExe -s -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $pipWheel.FullName (Join-Path $projectRoot ($runtimeName + '\Lib\site-packages'))
    if ($LASTEXITCODE -ne 0) { throw 'Pip bootstrap failed.' }
    & $pythonExe -s -m pip install --no-index --find-links (Join-Path $projectRoot $wheelsName) -r (Join-Path $projectRoot $requirementsName) --no-user --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw 'Pinned dependency installation failed.' }
}
& $pythonExe -s (Join-Path $PSScriptRoot 'setup_assets.py') @setupArgs
if ($LASTEXITCODE -ne 0) { throw 'Model verification or repair failed.' }
& $pythonExe -s -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
if ($Build) { & (Join-Path $PSScriptRoot 'build.ps1') -Architecture $Architecture }
Write-Output 'LectureLive setup and verification completed.'
