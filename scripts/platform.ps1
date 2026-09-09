# Shared, explicit build/runtime paths. Dot-source after declaring $Architecture.
if ($Architecture -eq 'auto') {
    $native = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITEW6432')
    if (-not $native) { $native = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE') }
    if ($native -eq 'ARM64') { $Architecture = 'ARM64' }
    elseif ($native -eq 'AMD64') { $Architecture = 'x64' }
    else { throw 'LectureLive supports Windows ARM64 and Windows x64 only.' }
}
$beta = $Architecture -eq 'x64'
$runtimeName = if ($beta) { 'runtime-x64' } else { 'runtime' }
$dependencyName = if ($beta) { 'dependencies-x64-beta.lock.json' } else { 'dependencies.lock.json' }
$requirementsName = if ($beta) { 'requirements-x64-beta-lock.txt' } else { 'requirements-lock.txt' }
$wheelsName = if ($beta) { 'offline_dependencies\wheels-x64' } else { 'offline_dependencies\wheels' }
$releaseName = if ($beta) { 'LectureLive-x64-Beta' } else { 'LectureLive' }
$pythonArchive = if ($beta) { '*embed-amd64.zip' } else { '*embed-arm64.zip' }
$modelsName = if ($beta) { 'assets-x64-beta.lock.json' } else { 'assets.lock.json' }
