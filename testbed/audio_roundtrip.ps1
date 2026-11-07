# Audio round trip for the voicemail stand-ins (laptop test, not part of the Skill).
# Speaks each voicemail transcript with a Windows text-to-speech voice into a WAV file, then
# transcribes the WAV with the offline Windows speech recognizer, so the identifier matching can be
# measured on machine-transcribed audio instead of on clean text.
#
# Usage (PowerShell): .\audio_roundtrip.ps1 -Corpus corpus\lakeside-dental -Out audio
# Writes <Out>\<name>.wav and <Out>\<name>.transcript.txt for each Voicemail\*.txt file.
param(
    [Parameter(Mandatory = $true)][string]$Corpus,
    [Parameter(Mandatory = $true)][string]$Out
)
Add-Type -AssemblyName System.Speech
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$files = Get-ChildItem -Path (Join-Path $Corpus 'Voicemail') -Filter *.txt | Sort-Object Name
foreach ($f in $files) {
    $text = Get-Content -LiteralPath $f.FullName -Raw
    # keep only what the caller says
    $spoken = ($text -split "`n" | Where-Object { $_ -match '^Caller:' }) -replace '^Caller:\s*', ''
    $wav = Join-Path $Out ($f.BaseName + '.wav')
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.SelectVoice('Microsoft Zira Desktop')
    $synth.Rate = 0
    $synth.SetOutputToWaveFile($wav)
    $synth.Speak(($spoken -join ' '))
    $synth.Dispose()

    $culture = New-Object System.Globalization.CultureInfo('en-US')
    $rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine($culture)
    $rec.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
    $rec.SetInputToWaveFile($wav)
    $parts = @()
    for ($i = 0; $i -lt 50; $i++) {
        try { $r = $rec.Recognize() } catch { break }   # the recognizer throws once the file is used up
        if ($null -eq $r) { break }
        $parts += $r.Text
    }
    $rec.Dispose()
    $transcript = ($parts -join ' ')
    Set-Content -LiteralPath (Join-Path $Out ($f.BaseName + '.transcript.txt')) -Value $transcript -Encoding utf8
    Write-Output ($f.Name + ' | ' + $transcript)
}
