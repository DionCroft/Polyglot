@echo off
setlocal
if not exist "%~dp0dist\LectureLive\LectureLive.exe" (
    echo LectureLive is not ready yet. Close this window and double-click Setup.cmd first.
    pause
    exit /b 1
)
start "" /D "%~dp0dist\LectureLive" "%~dp0dist\LectureLive\LectureLive.exe"
