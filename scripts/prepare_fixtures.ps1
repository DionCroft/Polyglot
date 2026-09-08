$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$fixtureRoot = Join-Path $projectRoot 'tests\fixtures'
New-Item -ItemType Directory -Path $fixtureRoot -Force | Out-Null
Add-Type -AssemblyName System.Speech
$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo -ArgumentList 16000, ([System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen), ([System.Speech.AudioFormat.AudioChannel]::Mono)
$cases = (Get-Content -LiteralPath (Join-Path $projectRoot 'docs\evidence\technical-benchmark.json') -Raw -Encoding UTF8 | ConvertFrom-Json).results
try {
    for ($index=0; $index -lt $cases.Count; $index++) {
        $targetPath = Join-Path $fixtureRoot ("technical-{0}.wav" -f $index)
        if (-not (Test-Path -LiteralPath $targetPath)) {
            $voice.SetOutputToWaveFile($targetPath, $format)
            $voice.Speak([string]$cases[$index].reference_english)
            $voice.SetOutputToNull()
        }
    }
    $combined = Join-Path $fixtureRoot 'technical.wav'
    if (-not (Test-Path -LiteralPath $combined)) {
        $body = ($cases | Select-Object -First 3 | ForEach-Object { [Security.SecurityElement]::Escape([string]$_.reference_english) + '<break time="800ms"/>' }) -join ' '
        $voice.SetOutputToWaveFile($combined, $format)
        $voice.SpeakSsml('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">' + $body + '</speak>')
        $voice.SetOutputToNull()
    }
} finally { $voice.Dispose() }
Write-Output 'Local synthetic PCM fixtures ready; existing fixtures were preserved.'
