@echo off
REM Double-click to build the Nimbus OS Linux ISO on Windows (needs Docker Desktop).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-windows.ps1" %*
pause
