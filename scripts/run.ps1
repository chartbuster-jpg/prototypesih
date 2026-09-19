# Start API + Streamlit for local demo
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = "."

Write-Host "Starting API on http://127.0.0.1:8000 ..."
Start-Process -FilePath "$Root\.venv\Scripts\uvicorn.exe" -ArgumentList "backend.app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $Root

Start-Sleep -Seconds 3
$env:API_BASE_URL = "http://127.0.0.1:8000"
Write-Host "Starting Streamlit on http://127.0.0.1:8501 ..."
& "$Root\.venv\Scripts\streamlit.exe" run frontend/streamlit_app.py --server.port 8501
