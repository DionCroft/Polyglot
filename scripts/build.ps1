param([ValidateSet('auto','ARM64','x64')][string]$Architecture = 'auto')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'platform.ps1')
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$releaseDir = [IO.Path]::GetFullPath((Join-Path $projectRoot ('dist\' + $releaseName)))
if (-not $releaseDir.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe build output path.' }
if ((Test-Path -LiteralPath $releaseDir) -and ((Get-Item -LiteralPath $releaseDir -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Build output must not be a junction or symlink.' }
$pythonExe = Join-Path $projectRoot ($runtimeName + '\python.exe')
$arguments = @('--noconfirm','--onedir','--windowed','--name',$releaseName,'--icon','assets/lecturelive.ico','--add-data','assets;assets','--collect-binaries','onnxruntime','--collect-data','opencc','--add-data','glossaries;glossaries','--add-data','docs;docs')
if ($beta) {
    & $pythonExe (Join-Path $PSScriptRoot 'stage_beta_models.py')
    if ($LASTEXITCODE -ne 0) { throw 'Beta model staging failed.' }
    $arguments += @('--collect-all','winui3','--collect-all','winrt','--add-data','build/beta-assets/models;models')
} else {
    $arguments += @('--collect-all','onnxruntime_qnn','--add-data','models/whisper;models/whisper','--add-data','models/translation/opus;models/translation/opus','--add-data','models/translation/opus-zh-en;models/translation/opus-zh-en','--add-data','models/vad;models/vad')
}
& $pythonExe -m PyInstaller @arguments LectureLive.pyw
if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
$exePath = Join-Path $releaseDir ($releaseName + '.exe')
& $pythonExe -c "import pefile,sys; p=pefile.PE(sys.argv[1]); expected=0x8664 if sys.argv[2]=='x64' else 0xAA64; print('PE machine:',hex(p.FILE_HEADER.Machine)); assert p.FILE_HEADER.Machine==expected" $exePath $Architecture
if ($LASTEXITCODE -ne 0) { throw 'Executable architecture verification failed.' }
$readme = if ($beta) { 'docs\BETA_READ_ME_FIRST.txt' } else { 'docs\PORTABLE_README.txt' }
Copy-Item -LiteralPath (Join-Path $projectRoot $readme) -Destination (Join-Path $releaseDir 'READ_ME_FIRST.txt') -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'STATUS.md') -Destination (Join-Path $releaseDir 'STATUS.md') -Force
