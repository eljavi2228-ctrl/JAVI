Set-Location $PSScriptRoot

$env:SUPABASE_URL = "https://sjsrspybbezhijbycxut.supabase.co"
$env:SUPABASE_KEY = "sb_publishable_vHWQhbWUwzy-I_eVWQYWsQ_M-L6eEKx"

$log = Join-Path $PSScriptRoot "streamlit_debug.log"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$bundledPython = "C:\Users\acost\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

"Starting Streamlit at $(Get-Date)" | Out-File -FilePath $log -Encoding utf8
"Working directory: $PSScriptRoot" | Out-File -FilePath $log -Append -Encoding utf8

try {
    if (-not (Test-Path $venvPython)) {
        if (Test-Path $bundledPython) {
            "Creating project venv from bundled Python: $bundledPython" | Out-File -FilePath $log -Append -Encoding utf8
            & $bundledPython -m venv (Join-Path $PSScriptRoot ".venv") *>> $log
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            "Creating project venv from system Python" | Out-File -FilePath $log -Append -Encoding utf8
            python -m venv (Join-Path $PSScriptRoot ".venv") *>> $log
        } else {
            "No Python found" | Out-File -FilePath $log -Append -Encoding utf8
            exit 1
        }
    }

    "Using project Python: $venvPython" | Out-File -FilePath $log -Append -Encoding utf8
    & $venvPython -c "import streamlit" *>> $log
    if ($LASTEXITCODE -ne 0) {
        "Installing requirements" | Out-File -FilePath $log -Append -Encoding utf8
        & $venvPython -m pip install --upgrade pip *>> $log
        & $venvPython -m pip install -r requirements.txt *>> $log
    }

    & $venvPython -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false *>> $log
} catch {
    $_ | Out-File -FilePath $log -Append -Encoding utf8
}

"Exited at $(Get-Date) with code $LASTEXITCODE" | Out-File -FilePath $log -Append -Encoding utf8
