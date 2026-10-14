@echo off
REM Coffee Origin Monitor - local launcher (Windows)
REM   dev.bat          demo mode: offline, synthetic data
REM   dev.bat live     real data from every free source, local archive
REM   dev.bat test     run the tests
REM   dev.bat reset    delete local archives (data\)
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=demo"
if "%PORT%"=="" set "PORT=8080"

if /i "%MODE%"=="reset" (
  if exist data rmdir /s /q data
  echo Deleted data\ - demo reseeds on next start.
  exit /b 0
)

if exist .venv\Scripts\python.exe goto :haveenv
echo Creating virtual environment...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m venv .venv
) else (
  python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo.
  echo Python 3.10 or newer is required. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during setup, then run dev.bat again.
  exit /b 1
)
:haveenv

.venv\Scripts\python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo This project needs Python 3.10+. Delete the .venv folder, install a newer Python, and retry.
  exit /b 1
)

if exist .venv\.deps-ok goto :havedeps
echo Installing dependencies (first run only, about a minute)...
.venv\Scripts\python -m pip install -q --upgrade pip
.venv\Scripts\python -m pip install -q -r requirements-local.txt
if errorlevel 1 (
  echo Dependency install failed. Check your internet connection and retry.
  exit /b 1
)
type nul > .venv\.deps-ok
:havedeps

if not exist .env (
  copy .env.example .env >nul
  echo Created .env from .env.example - edit it to add optional API keys.
)

if /i "%MODE%"=="test" (
  set "APP_MODE=demo"
  set "GDELT_DELAY=0"
  .venv\Scripts\python -m pytest -q tests
  exit /b
)

if /i not "%MODE%"=="demo" if /i not "%MODE%"=="live" (
  echo Usage: dev.bat [demo ^| live ^| test ^| reset]
  exit /b 1
)

echo.
echo   Coffee Origin Monitor - %MODE% mode
echo   http://localhost:%PORT%
if /i "%MODE%"=="demo" echo   Offline demo data. Run "dev.bat live" for real sources.
if /i "%MODE%"=="live" echo   First news run takes about a minute; watch the Sources and Dev pages.
echo   Press Ctrl+C to stop.
echo.
if not "%NO_BROWSER%"=="1" start "" /b cmd /c "timeout /t 3 /nobreak >nul & start "" http://localhost:%PORT%/"
set "APP_MODE=%MODE%"
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% --reload --reload-dir app --log-level warning
