# Build a self-contained onedir LiveCaptions-<version>.exe
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtualenv not found at $Python"
}

$AppName = & $Python -c "from version import APP_NAME; print(APP_NAME)"
if (-not $AppName) {
    throw "Could not read APP_NAME from version.py"
}

& $Python -m pip install -q pyinstaller
& $Python -m PyInstaller --noconfirm --clean LiveCaptions.spec

$OutDir = Join-Path $Root "dist\$AppName"
$Exe = Join-Path $OutDir "$AppName.exe"
if (-not (Test-Path $Exe)) {
    throw "Build failed: $Exe not created"
}

Copy-Item (Join-Path $Root "start-vlc1.cmd") $OutDir -Force
Copy-Item (Join-Path $Root "start-vlc2.cmd") $OutDir -Force
$DocsDir = Join-Path $OutDir "docs"
New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null
Copy-Item (Join-Path $Root "docs\SETUP_MULTICHANNEL.md") $DocsDir -Force

Write-Host "Built: $Exe"
Write-Host "Profiles: $OutDir\start-vlc1.cmd , $OutDir\start-vlc2.cmd"
