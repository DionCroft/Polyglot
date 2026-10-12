@echo off
setlocal
rem Works beside the portable EXE or in the extracted source/setup folder.
if exist "%~dp0LectureLive-x64-Beta.exe" (
    start "" /D "%~dp0" "%~dp0LectureLive-x64-Beta.exe" --cpu
    exit /b 0
)
if exist "%~dp0dist\LectureLive-x64-Beta\LectureLive-x64-Beta.exe" (
    start "" /D "%~dp0dist\LectureLive-x64-Beta" "%~dp0dist\LectureLive-x64-Beta\LectureLive-x64-Beta.exe" --cpu
    exit /b 0
)
echo Extract the whole Intel/AMD app ZIP first, including _internal.
echo If you downloaded source code, run Setup-Beta.cmd before using this launcher.
pause
exit /b 1
