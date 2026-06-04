$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:SUPABASE_URL = "https://sjsrspybbezhijbycxut.supabase.co"
$env:SUPABASE_KEY = "sb_publishable_vHWQhbWUwzy-I_eVWQYWsQ_M-L6eEKx"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$bundledPython = "C:\Users\acost\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (-not (Test-Path $venvPython)) {
    if (Test-Path $bundledPython) {
        Write-Host "Creando entorno virtual del proyecto..."
        & $bundledPython -m venv (Join-Path $PSScriptRoot ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Creando entorno virtual del proyecto..."
        python -m venv (Join-Path $PSScriptRoot ".venv")
    } else {
        Write-Host "No se encontro Python. Instala Python 3.11+ y ejecuta: pip install -r requirements.txt"
        exit 1
    }
}

& $venvPython -c "import streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando dependencias del proyecto. Esto puede tardar unos minutos..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
}

if ($LASTEXITCODE -eq 0) {
    & $venvPython -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
} else {
    Write-Host "No se pudieron instalar las dependencias. Revisa la conexion a internet y vuelve a ejecutar INICIAR_APP.bat."
    exit 1
}
