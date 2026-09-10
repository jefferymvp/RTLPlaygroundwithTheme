@echo off
setlocal
title RTLPlayground Theme Patch Tool

where powershell >nul 2>&1
if %errorlevel% equ 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply_theme_patch.ps1" %*
    exit /b %errorlevel%
)

echo [ERROR] PowerShell is required to run this patch tool.
pause
exit /b 1
