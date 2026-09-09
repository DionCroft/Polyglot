@echo off
setlocal
if not exist "%~dp0dist\LectureLive-x64-Beta\LectureLive-x64-Beta.exe" (
    echo First double-click Setup-Beta.cmd and wait for setup to finish.
    pause
    exit /b 1
)
start "" /D "%~dp0dist\LectureLive-x64-Beta" "%~dp0dist\LectureLive-x64-Beta\LectureLive-x64-Beta.exe"
