@echo off
setlocal
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is required to run this launcher. Install Node.js and try again.
  pause
  exit /b 1
)
node "%~dp0setup\start-multica.mjs" %*
set "result=%errorlevel%"
if not "%result%"=="0" pause
exit /b %result%
