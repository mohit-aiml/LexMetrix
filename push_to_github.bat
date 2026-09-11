@echo off
setlocal
title LexMetrix - GitHub Uploader
cls
echo =====================================================================
echo                 LexMetrix - 1-Click GitHub Uploader
echo =====================================================================
echo.

set "GIT_CMD=C:\Users\mohit\AppData\Local\GitHubDesktop\app-3.6.4\resources\app\git\cmd\git.exe"

if not exist "%GIT_CMD%" (
    echo [ERROR] Git path nahi mila.
    pause
    exit /b 1
)

echo [Step 1] Agar aapne abhi tak GitHub par new repository nahi banayi hai,
echo         toh pehle browser me https://github.com/new par jakar bana lein.
echo.
set /p REPO_URL="[Step 2] Apna GitHub Repository URL paste karein aur Enter dabayein: "

if "%REPO_URL%"=="" (
    echo.
    echo [ERROR] URL khali chhod diya aapne!
    echo Script dobara chalayein aur valid URL paste karein.
    pause
    exit /b 1
)

echo.
echo [Step 3] Remote repository link kar rahe hain...
"%GIT_CMD%" remote remove origin >nul 2>&1
"%GIT_CMD%" remote add origin %REPO_URL%
"%GIT_CMD%" branch -M main

echo.
echo [Step 4] Code GitHub par upload (push) ho raha hai...
echo (Agar browser popup aaye toh "Sign in with browser" click kar dena)
echo.

"%GIT_CMD%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =====================================================================
    echo   BADHAI HO! Aapka pura LexMetrix project GitHub par upload ho gaya!
    echo =====================================================================
) else (
    echo.
    echo =====================================================================
    echo   Upload fail ho gaya. Check karein ki URL sahi tha aur internet ON hai.
    echo =====================================================================
)

echo.
pause
