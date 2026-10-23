$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install requirements.txt first. See README.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\node_modules'))) {
    throw 'Run npm.cmd ci inside frontend first. See README.md.'
}
$logDirectory = Join-Path $projectRoot 'output'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$backendProcess = Start-Process -FilePath $pythonPath -ArgumentList @('manage.py','runserver','127.0.0.1:8000','--noreload') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'backend.log') -RedirectStandardError (Join-Path $logDirectory 'backend-error.log')
Write-Host 'Wayfinder: http://localhost:5173 (Ctrl+C stops this development session).'
Push-Location (Join-Path $projectRoot 'frontend')
try {
    & npm.cmd run dev -- --host 127.0.0.1
} finally {
    Pop-Location
    if (-not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    }
}
