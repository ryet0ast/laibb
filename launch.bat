@echo off
setlocal
title GPT Builder Wizard

echo.
echo  =====================================================
echo   Custom GPT Builder — Search Strategy Assistant
echo  =====================================================
echo.

cd /d "%~dp0"

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [setup] Installing uv — this only happens once...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

echo Starting wizard...
echo.
echo  Opening http://localhost:8503 in your browser.
echo  To stop: close this window or press Ctrl+C
echo.
start "" http://localhost:8503
uv run streamlit run app.py --server.port 8503 --server.headless true --browser.gatherUsageStats false

endlocal
