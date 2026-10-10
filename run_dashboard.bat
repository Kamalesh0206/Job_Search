@echo off
title AI Engineer Job Search & Auto-Apply Dashboard
echo ========================================================
echo   AI Engineer Job Search & Auto-Apply Agent Dashboard
echo   Candidate: Kamalesan C (7.4y Exp, AI Engineer)
echo ========================================================
echo.
echo Launching server at http://127.0.0.1:8000 ...
timeout /t 2 >nul
start http://127.0.0.1:8000
python server.py
pause
