@echo off
setlocal
cd /d "%~dp0"
if exist "LiveCaptions-v0.5.0.exe" (
  start "" "%~dp0LiveCaptions-v0.5.0.exe" --profile vlc2
  exit /b 0
)
if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" app.py --profile vlc2
  exit /b 0
)
echo Start LiveCaptions-v0.5.0.exe of run.cmd eerst.
exit /b 1
