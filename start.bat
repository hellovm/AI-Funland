@echo off
setlocal
set WORKDIR=%~dp0
cd /d "%WORKDIR%"
set PYTHONPATH=%WORKDIR%

if not exist .venv (
  where py >nul 2>nul
  if %ERRORLEVEL%==0 (
    py -3.11 -m venv .venv
  ) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
      python -m venv .venv
    )
  )
)

if not exist .venv\Scripts\python.exe (
  if not exist python-embed\python.exe (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$url='https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip'; $zip='python-embed.zip'; Invoke-WebRequest -Uri $url -OutFile $zip; Expand-Archive -Force $zip -DestinationPath 'python-embed'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python-embed/get-pip.py'" 
    if exist python-embed\python.exe (
      python-embed\python.exe python-embed\get-pip.py
    )
  )
)

if exist python-embed\python311._pth (
  findstr /C:"." python-embed\python311._pth >nul || (echo .>> python-embed\python311._pth)
  findstr /C:".." python-embed\python311._pth >nul || (echo ..>> python-embed\python311._pth)
  findstr /C:"import site" python-embed\python311._pth >nul || (echo import site>> python-embed\python311._pth)
)

set PY=.venv\Scripts\python.exe
if not exist %PY% (
  set PY=python-embed\python.exe
)

if exist requirements.txt (
  %PY% -m pip install -r requirements.txt
)

rem Cleanup invalid torch leftovers
for /d %%d in ("python-embed\Lib\site-packages\~orch*") do rd /s /q "%%d" 2>nul

rem Torch version auto-detect and install (batch-based)
set TORCH_TARGET=2.4.0
set TORCH_VER=
for /f "tokens=2 delims= " %%v in ('%PY% -m pip show torch ^| findstr /R "^Version"') do set TORCH_VER=%%v
set TORCH_MM=
for /f "tokens=1,2 delims=." %%a in ("%TORCH_VER%") do set TORCH_MM=%%a.%%b
set TORCH_TARGET_MM=
for /f "tokens=1,2 delims=." %%a in ("%TORCH_TARGET%") do set TORCH_TARGET_MM=%%a.%%b
if "%TORCH_MM%"=="" (
  echo [setup] torch not found
) else (
  echo [setup] torch installed: %TORCH_VER%
)
if /I not "%TORCH_MM%"=="%TORCH_TARGET_MM%" (
  echo [setup] installing torch %TORCH_TARGET%
  %PY% -m pip install "torch==%TORCH_TARGET%"
) else (
  echo [setup] torch version OK: %TORCH_VER%
)

start "AI Funland" http://127.0.0.1:8000/
%PY% -m backend.app
endlocal