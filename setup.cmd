@echo off
setlocal DisableDelayedExpansion
rem Bypass applies only to this PowerShell process; machine/user policy is unchanged.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installers\setup-windows.ps1" %*
set "setup_exit=%errorlevel%"
if not "%setup_exit%"=="0" echo Setup failed. Review the message above before retrying.
pause
exit /b %setup_exit%
