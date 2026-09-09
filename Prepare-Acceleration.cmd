@echo off
setlocal
cd /d "%~dp0"
if not exist "runtime-x64\python.exe" (
    echo First run Setup-Beta.cmd. See docs\WINDOWS_BETA.md for help.
    pause
    exit /b 1
)
echo This optional ONLINE setup downloads compatible Intel/AMD NPU providers.
echo It does not start a lecture or record microphone audio.
echo Keep this window open. CPU and compatible GPU captions need no NPU setup.
"runtime-x64\python.exe" -X utf8 scripts\prepare_acceleration.py
set "prepare_result=%errorlevel%"
echo.
if not "%prepare_result%"=="0" echo Read docs\WINDOWS_BETA.md for Windows App Runtime and driver instructions.
pause
exit /b %prepare_result%
