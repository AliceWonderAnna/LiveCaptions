@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
py -3.12 -c "import sys; assert sys.maxsize > 2**32" >nul 2>&1
if not errorlevel 1 (
  py -3.12 -m venv .venv
  goto checkvenv
)
py -3.11 -c "import sys; assert sys.maxsize > 2**32" >nul 2>&1
if not errorlevel 1 (
  py -3.11 -m venv .venv
  goto checkvenv
)
python -c "import sys; assert (3,11) <= sys.version_info[:2] <= (3,13) and sys.maxsize > 2**32" >nul 2>&1
if errorlevel 1 goto nopython
python -m venv .venv
:checkvenv
if not exist ".venv\Scripts\python.exe" goto failed
:install
if exist ".venv\installed.ok" goto launch
echo Eerste installatie. Dit kan enkele minuten duren...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo installed>".venv\installed.ok"
:launch
".venv\Scripts\python.exe" app.py %*
if errorlevel 1 goto failed
exit /b 0
:nopython
echo Installeer Python 3.12 64-bit vanaf https://www.python.org/downloads/windows/
echo Vink de Python launcher en Add python.exe to PATH aan. Start dit bestand daarna opnieuw.
pause
exit /b 1
:failed
echo.
echo Starten of installeren mislukt. Lees de fout hierboven en README.md.
pause
exit /b 1
