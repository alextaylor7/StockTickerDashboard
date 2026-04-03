param(
    [string]$AppName = "StockTickerDashboard",
    [string]$VenvDir = ".venv-build"
)

$ErrorActionPreference = "Stop"

function Get-VenvPython {
    param([string]$Path)
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        return Join-Path $Path "Scripts/python.exe"
    }
    return Join-Path $Path "bin/python"
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$venvPython = Get-VenvPython -Path $VenvDir

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating build virtual environment at $VenvDir ..."
    py -3 -m venv $VenvDir
}

$venvPython = Get-VenvPython -Path $VenvDir

Write-Host "Installing/upgrading build dependencies ..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install pyinstaller
& $venvPython -m pip install -r requirements.txt

Write-Host "Cleaning previous build output ..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "$AppName.spec") { Remove-Item -Force "$AppName.spec" }

Write-Host "Building executable with PyInstaller ..."
& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --name $AppName `
    --onedir `
    --hidden-import waitress `
    --add-data "assets;assets" `
    --add-data "pages;pages" `
    --add-data "callbacks;callbacks" `
    main.py

$distDir = Join-Path $repoRoot "dist\$AppName"
$exePath = Join-Path $distDir "$AppName.exe"

if (-not (Test-Path $exePath)) {
    throw "Build finished but executable not found at $exePath"
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable: $exePath"
Write-Host "Run: .\dist\$AppName\$AppName.exe"
Write-Host "Open in browser: http://127.0.0.1:8050"
Write-Host "Session file location at runtime: .\dist\$AppName\data\session_state.json"
