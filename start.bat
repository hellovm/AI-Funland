@echo off
setlocal
set PROJECT_DIR=%~dp0
set AIFUNLAND_CACHE_DIR=%PROJECT_DIR%\tmp
set PY_VERSION=3.11.9
set PY_DIR=%PROJECT_DIR%\.python
set PY_EMBED_ZIP=python-%PY_VERSION%-embed-amd64.zip
set PY_URL=https://www.python.org/ftp/python/%PY_VERSION%/%PY_EMBED_ZIP%

if not exist "%PY_DIR%" mkdir "%PY_DIR%"

if not exist "%PY_DIR%\python.exe" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_DIR%\%PY_EMBED_ZIP%'"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%PY_DIR%\%PY_EMBED_ZIP%' -DestinationPath '%PY_DIR%' -Force"
  del "%PY_DIR%\%PY_EMBED_ZIP%" >nul 2>&1
)

if exist "%PY_DIR%\python.exe" (
  for /f "tokens=2 delims=." %%v in ("%PY_VERSION%") do set MAJOR=%%v
)

set PTH_FILE=%PY_DIR%\python311._pth
if not exist "%PTH_FILE%" set PTH_FILE=%PY_DIR%\python312._pth
if exist "%PTH_FILE%" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Content '%PTH_FILE%') -replace '^#import site','import site' | Set-Content '%PTH_FILE%'"
)

rem Check pip availability in embedded Python
"%PY_DIR%\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PY_DIR%\get-pip.py'"
  "%PY_DIR%\python.exe" "%PY_DIR%\get-pip.py"
)

"%PY_DIR%\python.exe" -m pip install --upgrade pip setuptools wheel
"%PY_DIR%\python.exe" -m pip install -r "%PROJECT_DIR%\requirements.txt"

rem Start backend using script path to include project on sys.path
start "AI Funland" "%PY_DIR%\python.exe" "%PROJECT_DIR%\backend\app.py"

rem Wait briefly then open browser (retry if not ready)
set /a RETRIES=0
:retry_open
timeout /t 2 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/).StatusCode } catch { 0 }" > "%TEMP%\aifunland_status.txt"
for /f "usebackq delims=" %%s in ("%TEMP%\aifunland_status.txt") do set STATUS=%%s
if "%STATUS%"=="200" (
  start http://127.0.0.1:8000/
) else (
  set /a RETRIES+=1
  if %RETRIES% LSS 5 goto retry_open
  start http://127.0.0.1:8000/
)
exit /b 0