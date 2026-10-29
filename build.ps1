# Build a self-contained onedir LiveCaptions-<version>.exe and an upgradeable Setup.exe
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
$Version = & $Python -c "from version import VERSION; print(VERSION)"
if (-not $Version) {
    throw "Could not read VERSION from version.py"
}

& $Python (Join-Path $Root "scripts\sync_version.py")
if ($LASTEXITCODE -ne 0) {
    throw "sync_version.py failed"
}

& $Python -m pip install -q pyinstaller
& $Python -m PyInstaller --noconfirm --clean LiveCaptions.spec

$OutDir = Join-Path $Root "dist\$AppName"
$Exe = Join-Path $OutDir "$AppName.exe"
if (-not (Test-Path $Exe)) {
    throw "Build failed: $Exe not created"
}

$RuntimeDir = Join-Path $OutDir "runtime"
if (-not (Test-Path $RuntimeDir)) {
    throw "Build failed: runtime folder missing at $RuntimeDir (expected contents_directory=runtime)"
}
if (Test-Path (Join-Path $OutDir "_internal")) {
    throw "Build failed: unexpected _internal folder; contents_directory was not applied"
}

Copy-Item (Join-Path $Root "start-vlc1.cmd") $OutDir -Force
Copy-Item (Join-Path $Root "start-vlc2.cmd") $OutDir -Force
$DocsDir = Join-Path $OutDir "docs"
New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null
Copy-Item (Join-Path $Root "docs\SETUP_MULTICHANNEL.md") $DocsDir -Force

Write-Host "Built: $Exe"
Write-Host "Profiles: $OutDir\start-vlc1.cmd , $OutDir\start-vlc2.cmd"

function Find-ISCC {
    $candidates = @(
        (Get-Command iscc -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }
    return $candidates | Select-Object -First 1
}

$Iscc = Find-ISCC
if (-not $Iscc) {
    throw "Inno Setup 6 (ISCC.exe) not found. Install with: winget install JRSoftware.InnoSetup"
}

$Iss = Join-Path $Root "installer\LiveCaptions.iss"
$Setup = Join-Path $Root "dist\LiveCaptions-v$Version-Setup.exe"
if (Test-Path $Setup) {
    Remove-Item $Setup -Force
}

& $Iscc "/DMyAppVersion=$Version" "/DMyAppName=$AppName" $Iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compile failed (exit $LASTEXITCODE)"
}
if (-not (Test-Path $Setup)) {
    throw "Setup exe not created: $Setup"
}

Write-Host "Setup: $Setup"
