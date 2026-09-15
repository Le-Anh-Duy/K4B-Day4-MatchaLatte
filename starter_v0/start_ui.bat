@echo off
setlocal
cd /d "%~dp0"
echo Starting Matcha IT Helpdesk...
echo Open http://127.0.0.1:8011 in your browser.
python ui_server.py --provider gemini --version v3 --port 8011 --open-browser
if errorlevel 1 (
  echo.
  echo Could not start. Install dependencies with: pip install -r requirements.txt
  pause
)
endlocal
