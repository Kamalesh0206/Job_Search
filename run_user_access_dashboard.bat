@echo off
title AccessHub - User Access & Host Management Dashboard
echo =================================================================
echo   AccessHub: Enterprise User Access & Host Management Portal
echo   Current Host Name: %COMPUTERNAME%
echo =================================================================
echo.
echo Launching dashboard server at http://127.0.0.1:8080 ...
echo Network Host URL: http://%COMPUTERNAME%:8080
echo.
timeout /t 2 >nul
start http://127.0.0.1:8080
python user_access_server.py
pause
