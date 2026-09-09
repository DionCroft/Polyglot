$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$releaseDir = [IO.Path]::GetFullPath((Join-Path $projectRoot 'dist\LectureLive'))
if (-not $releaseDir.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Unsafe build output path.' }
if ((Test-Path -LiteralPath $releaseDir) -and ((Get-Item -LiteralPath $releaseDir -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Build output must not be a junction or symlink.' }
& "$projectRoot\runtime\python.exe" -m PyInstaller --noconfirm --onedir --windowed --name LectureLive --icon assets/lecturelive.ico --add-data "assets;assets" --collect-all onnxruntime_qnn --collect-binaries onnxruntime --collect-data opencc --add-data 'models/whisper;models/whisper' --add-data 'models/translation/opus;models/translation/opus' --add-data 'models/vad;models/vad' --add-data 'glossaries;glossaries' --add-data 'docs;docs' LectureLive.pyw
if ($LASTEXITCODE -ne 0) { throw 'Native application build failed.' }
& "$projectRoot\runtime\python.exe" -c "import pefile; p=pefile.PE('dist/LectureLive/LectureLive.exe'); print('PE machine:',hex(p.FILE_HEADER.Machine)); assert p.FILE_HEADER.Machine==0xAA64"
if ($LASTEXITCODE -ne 0) { throw 'Executable is not ARM64.' }

Copy-Item -LiteralPath (Join-Path $projectRoot 'docs\PORTABLE_README.txt') -Destination (Join-Path $releaseDir 'READ_ME_FIRST.txt') -Force
Copy-Item -LiteralPath (Join-Path $projectRoot 'STATUS.md') -Destination (Join-Path $releaseDir 'STATUS.md') -Force
