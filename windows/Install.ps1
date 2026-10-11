$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (!(Get-Command py -ErrorAction SilentlyContinue)) { throw 'Install Python 3.11 x64 from python.org with the Python launcher, then retry.' }
& py -3.11 -c "import struct; assert struct.calcsize('P') == 8, 'Python x64 required'"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 x64 is required.' }
& py -3.11 -m venv (Join-Path $projectRoot '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Unable to create Python environment.' }
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $pythonExe -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $pythonExe -c "import cv2,mediapipe,PIL; print('Webcam dependencies ready')"
if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed.' }
Write-Host 'Setup complete. In Rhino 8 run: -ScriptEditor Run'
Write-Host ('Then select: ' + (Join-Path $PSScriptRoot 'OpenPanel.py'))
