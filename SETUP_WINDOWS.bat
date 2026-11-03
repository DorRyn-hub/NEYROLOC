@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo Install Python 3.12 (64-bit) with the Python launcher, then retry.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install -r NEYROLOCK_5\requirements.txt
if errorlevel 1 goto :failed
echo Setup complete. Run START_WINDOWS.bat.
echo Local GGUF inference requires a separate llama-cpp-python installation.
pause
exit /b 0
:failed
echo Setup failed. Review the error above before starting the application.
pause
exit /b 1
