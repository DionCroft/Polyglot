param([ValidateSet('auto','ARM64','x64')][string]$Architecture = 'auto')
. (Join-Path $PSScriptRoot 'platform.ps1')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $projectRoot ('dist\' + $releaseName + '\' + $releaseName + '.exe')
if (-not (Test-Path -LiteralPath $exe)) { throw 'Build LectureLive first.' }
$menu = [Environment]::GetFolderPath('Programs')
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $menu ($releaseName + '.lnk')))
$link.TargetPath = $exe
$link.WorkingDirectory = Split-Path -Parent $exe
$link.Description = 'Offline bilingual live captions for teaching'
$link.Save()
Write-Output 'Created LectureLive Start Menu shortcut.'
