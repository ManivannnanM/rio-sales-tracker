@echo off
cls

echo =====================================================
echo   RIO PRINT MEDIA ERP v2.0 - Deploy to Render
echo   PRODUCTION
echo =====================================================
echo.

cd /d "%~dp0"
echo [INFO] Working directory: %cd%
echo.

:: Check required files
if not exist "RIO_PRINT_MEDIA_ERP.html" (
    echo [ERROR] Missing file: RIO_PRINT_MEDIA_ERP.html
    pause
    exit /b
)

if not exist "rio_erp_api.py" (
    echo [ERROR] Missing file: rio_erp_api.py
    pause
    exit /b
)

if not exist "requirements.txt" (
    echo [ERROR] Missing file: requirements.txt
    pause
    exit /b
)

echo [OK] All required files found.
echo.

:: Init git if needed
if not exist ".git" (
    git init
    echo [OK] Git initialized.
) else (
    echo [INFO] Git repo already exists.
)

echo.

:: Clean git state
echo [INFO] Cleaning git state...
git merge --abort >nul 2>&1
git reset --hard >nul 2>&1

echo.

:: Add files
git add .

:: Commit
git commit -m "Deploy RIO PRINT MEDIA ERP v2.0" >nul 2>&1

if %errorlevel% neq 0 (
    echo [INFO] No changes to commit.
) else (
    echo [OK] Commit created.
)

echo.

:: Fix remote
git remote remove origin >nul 2>&1
git remote add origin https://github.com/rioprintmediaa/rio-print-media.git

:: Branch
git branch -M main

echo.

:: Push
git push -u origin main --force

echo.
echo =====================================================
echo   DEPLOYMENT SUCCESS
echo =====================================================
pause