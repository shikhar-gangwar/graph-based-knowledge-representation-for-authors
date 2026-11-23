@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0;%PYTHONPATH%
echo ==============================================================
echo   ScholarlyKG - Research Collaboration Analytics Dashboard
echo ==============================================================
echo Starting server on http://127.0.0.1:8000 ...
python "%~dp0run_dashboard.py"
pause
