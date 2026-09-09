@echo off
setlocal
set "native_arch=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "native_arch=%PROCESSOR_ARCHITEW6432%"
if /I "%native_arch%"=="AMD64" (
    call "%~dp0Launch-Beta.cmd"
    exit /b
)
if not exist "%~dp0dist\LectureLive\LectureLive.exe" (
    echo LectureLive is not ready yet. Close this window and double-click Setup.cmd first.
    pause
    exit /b 1
)
start "" /D "%~dp0dist\LectureLive" "%~dp0dist\LectureLive\LectureLive.exe"
