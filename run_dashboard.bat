@echo off
title Dual-Role AI Job Search & Application Automation Dashboard
echo ====================================================================
echo   Dual-Role AI Job Search & Application Automation Agent
echo   Candidate: Kamalesan C (7.4y Experience)
echo   Profiles: [AI Engineer] ^& [Automotive Test Engineer]
echo ====================================================================
echo.
echo   Dashboard Access URLs:
echo     - http://localhost:8000      (Local Loopback)
echo     - http://%COMPUTERNAME%:8000  (Local Network Host Name)
echo.
echo Launching server at http://localhost:8000 ...
timeout /t 2 >nul
start http://localhost:8000
python server.py
pause
