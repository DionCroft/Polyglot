@echo off
call "%~dp0Setup.cmd" -Architecture x64 %*
exit /b %errorlevel%
