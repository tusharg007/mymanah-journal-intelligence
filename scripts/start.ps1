$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
if (Test-Path -LiteralPath "$root\artifacts\ollama\ollama.exe") {
    $env:PATH = "$root\artifacts\ollama;$env:PATH"
}
$env:OLLAMA_MODELS = "$root\models\ollama"
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NO_CLOUD = '1'
# Measured laptop profile: keep the 4B model on the 4 GB GPU instead of pinning extra host RAM.
if (-not $env:LLAMA_ARG_FIT_TARGET) { $env:LLAMA_ARG_FIT_TARGET = '256' }
try {
    Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null
} catch {
    $ollama = (Get-Command ollama -ErrorAction Stop).Source
    Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput "$root\artifacts\ollama-stdout.log" -RedirectStandardError "$root\artifacts\ollama-stderr.log"
}
& "$root\.venv\Scripts\python.exe" "$root\scripts\start.py"
