$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $projectRoot 'dist\LectureLive\LectureLive.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw 'Build LectureLive first.' }
$menu = [Environment]::GetFolderPath('Programs')
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $menu 'LectureLive.lnk'))
$link.TargetPath = $exe
$link.WorkingDirectory = Split-Path -Parent $exe
$link.Description = 'Offline bilingual live captions for teaching'
$link.Save()
Write-Output 'Created LectureLive Start Menu shortcut.'
