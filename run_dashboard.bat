@echo off
title Dual-Role AI Job Search & Application Automation Dashboard
echo ====================================================================
echo   Dual-Role AI Job Search & Application Automation Agent
echo   Candidate: Kamalesan C (7.4y Experience)
echo   Profiles: [AI Engineer] ^& [Automotive Test Engineer]
echo ====================================================================
echo.
echo   Host Name Access URLs:
echo     - http://%COMPUTERNAME%:8000  (Active Windows Host Name)
echo     - http://jobagent.local:8000 (Custom Host Alias)
echo     - http://localhost:8000      (Local Loopback)
echo.
echo Launching server at http://%COMPUTERNAME%:8000 ...
timeout /t 2 >nul
start http://%COMPUTERNAME%:8000
python server.py
pause
