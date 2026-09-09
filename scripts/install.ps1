param([switch]$Offline, [switch]$NoShortcut, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$transcribing = $false
try {
    Start-Transcript -LiteralPath (Join-Path $projectRoot 'setup.log') -Force | Out-Null
    $transcribing = $true
    Write-Host 'LectureLive - first-time setup' -ForegroundColor Cyan
    Write-Host 'Step 1 of 3: checking this computer and the extracted folder.'
    $nativeArchitecture = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITEW6432')
    if (-not $nativeArchitecture) { $nativeArchitecture = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE') }
    if ($nativeArchitecture -ne 'ARM64') {
        throw 'This release needs a Windows 11 PC with a Snapdragon ARM64 processor. Intel/AMD (x64) PCs and Macs are not supported by this installer. See README.md.'
    }
    $windowsBuild = [Environment]::OSVersion.Version.Build
    if ($windowsBuild -lt 22000) { throw 'Windows 11 is required for this release.' }
    foreach ($name in @('app\main.py', 'assets\lecturelive.ico', 'scripts\setup.ps1', 'dependencies.lock.json', 'assets.lock.json')) {
        if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $name))) { throw 'Extract the whole download first, then open Setup.cmd inside the extracted folder.' }
    }
    if (Get-Process -Name LectureLive -ErrorAction SilentlyContinue) { throw 'Close LectureLive before running setup or repair, then try again.' }
    $probe = Join-Path $projectRoot ('.setup-write-test-' + [Guid]::NewGuid().ToString('N'))
    [IO.File]::WriteAllText($probe, 'writable')
    Remove-Item -LiteralPath $probe
    Write-Host 'Computer and folder checks passed.' -ForegroundColor Green
    if ($CheckOnly) { return }
    Write-Host 'Step 2 of 3: preparing the app. The first run downloads several GB and can take a while.'
    Write-Host 'Already verified downloads are reused when you run setup again.'
    $arguments = @{}
    if ($Offline) { $arguments.Offline = $true }
    & (Join-Path $PSScriptRoot 'setup.ps1') -Build @arguments
    Write-Host 'Step 3 of 3: creating your launcher.'
    if (-not $NoShortcut) {
        try { & (Join-Path $PSScriptRoot 'install-shortcut.ps1') }
        catch { Write-Warning ('The app is ready, but the Start menu shortcut could not be created. Use Launch.cmd. ' + $_.Exception.Message) }
    }
    Write-Host ''
    Write-Host 'SETUP COMPLETE' -ForegroundColor Green
    Write-Host 'Double-click Launch.cmd in this folder, or find LectureLive in the Windows Start menu.'
    Write-Host 'Keep this folder: the launcher and its local models live here.'
    Write-Host 'Your first steps are in README.md. No Python installation or account is needed.'
} catch {
    Write-Host ''
    Write-Host ('SETUP STOPPED: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Read README.md for help. Technical details are in setup.log in this folder.'
    exit 1
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
}
