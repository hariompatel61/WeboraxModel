@echo off
:: ============================================
:: Sets up WeboraxModel Video Scheduler to
:: auto-start on Windows login (no approval needed)
:: ============================================
:: Run this ONCE as Administrator

echo Setting up auto-start for WeboraxModel Video Scheduler...

schtasks /create /tn "WeboraxModel_VideoScheduler" /tr "pythonw \"%~dp0scheduler.py\"" /sc onlogon /rl highest /f

if %errorlevel%==0 (
    echo.
    echo ============================================
    echo   SUCCESS! Scheduler will auto-start on login.
    echo   Videos upload at 7:00 AM and 7:00 PM IST.
    echo   No approval or input needed - ever!
    echo ============================================
) else (
    echo.
    echo FAILED - Please right-click this file and "Run as Administrator"
)

pause
