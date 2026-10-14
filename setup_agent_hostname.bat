@echo off
setlocal EnableDelayedExpansion
title Setup Agent Host Name (jobagent.local)

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo =================================================================
    echo   Requesting Administrator Privileges to configure host name...
    echo =================================================================
    powershell -NoProfile -Command "Start-Process cmd.exe -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo =================================================================
echo   Configuring Local Host Name for AI Job Search Agent
echo =================================================================
echo.

set HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts
set HOST_ENTRY=127.0.0.1  jobagent.local
set HOST_ALIAS=127.0.0.1  ai-agent.local

:: Check if already exists in hosts file
findstr /i /c:"jobagent.local" "%HOSTS_FILE%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Host name 'jobagent.local' is already configured in Windows hosts file!
) else (
    echo Appending 'jobagent.local' mapping to %HOSTS_FILE% ...
    echo. >> "%HOSTS_FILE%"
    echo # Dual-Role AI Job Search and Application Automation Agent >> "%HOSTS_FILE%"
    echo %HOST_ENTRY% >> "%HOSTS_FILE%"
    echo %HOST_ALIAS% >> "%HOSTS_FILE%"
    echo [SUCCESS] Host names added successfully!
)

:: Flush DNS resolver cache
ipconfig /flushdns >nul 2>&1

echo.
echo =================================================================
echo   Access URLs now available:
echo     - http://jobagent.local:8000
echo     - http://ai-agent.local:8000
echo     - http://%COMPUTERNAME%:8000
echo =================================================================
echo.

timeout /t 2 >nul
start http://jobagent.local:8000
pause
