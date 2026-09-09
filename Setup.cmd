@echo off
setlocal
cd /d "%~dp0"
echo.
echo LectureLive setup for Windows 11 (Snapdragon ARM64 or Intel/AMD x64 beta)
echo Keep this window open until setup finishes.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1" %*
set "setup_result=%errorlevel%"
echo.
if not "%setup_result%"=="0" echo Setup did not finish. Read the message above or open setup.log in this folder.
pause
exit /b %setup_result%
