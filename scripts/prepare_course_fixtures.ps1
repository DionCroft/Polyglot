$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$cases = (Get-Content -LiteralPath (Join-Path $projectRoot 'tests\fixtures\co7000-cases.json') -Raw -Encoding UTF8 | ConvertFrom-Json).cases
Add-Type -AssemblyName System.Speech
$courseVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo -ArgumentList 16000, ([System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen), ([System.Speech.AudioFormat.AudioChannel]::Mono)
try {
    $voiceName = $courseVoice.Voice.Name
    $culture = $courseVoice.Voice.Culture.Name
    $generated = @()
    foreach ($case in $cases) {
        $target = [IO.Path]::GetFullPath((Join-Path $projectRoot $case.path))
        $allowed = [IO.Path]::GetFullPath((Join-Path $projectRoot 'tests\fixtures')) + [IO.Path]::DirectorySeparatorChar
        if (-not $target.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe fixture path' }
        if (-not (Test-Path -LiteralPath $target)) {
            $courseVoice.SetOutputToWaveFile($target, $format)
            $courseVoice.Speak([string]$case.reference)
            $courseVoice.SetOutputToNull()
            $generated += $case.id
        }
    }
    $artifacts = Join-Path $projectRoot 'tests\artifacts'
    New-Item -ItemType Directory -Path $artifacts -Force | Out-Null
    $report = @{voice=$voiceName; culture=$culture; generated=$generated; synthetic=$true; live_microphone=$false}
    $report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $artifacts 'co7000-fixture-voice.json') -Encoding UTF8
    $report | ConvertTo-Json
} finally { $courseVoice.Dispose() }
