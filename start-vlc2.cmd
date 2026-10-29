@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0LiveCaptions-v*.exe" (
  for %%F in ("%~dp0LiveCaptions-v*.exe") do (
    start "" "%%~fF" --profile vlc2
    exit /b 0
  )
)
if exist ".venv\Scripts\python.exe" (
  start "" ".venv\Scripts\python.exe" app.py --profile vlc2
  exit /b 0
)
echo Start LiveCaptions-v*.exe of run.cmd eerst.
exit /b 1
