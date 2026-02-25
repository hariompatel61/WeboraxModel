@echo off
title WeboraxModel - Video Scheduler (7 AM & 7 PM IST)
echo ============================================
echo   WeboraxModel Automated Video Scheduler
echo   Videos will upload at 7:00 AM ^& 7:00 PM
echo ============================================
echo.

cd /d "%~dp0"
python scheduler.py

pause
