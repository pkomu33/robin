$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Missing .venv. Create it first with: python -m venv .venv"
    exit 1
}

& $Python -c "import streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Streamlit is not installed in .venv. Run: .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt"
    exit 1
}

if (-not (Test-Path (Join-Path $PSScriptRoot ".env"))) {
    Write-Warning "No .env file found. Copy .env.example to .env or provide configuration through shell environment variables."
}

& $Python -m streamlit run ui.py
exit $LASTEXITCODE
