@echo off
REM Quick pgvector setup script for Windows
REM Run this after building pgvector with nmake

echo.
echo ========================================
echo  pgvector Quick Setup
echo ========================================
echo.

REM Step 1: Restart PostgreSQL
echo [1/3] Restarting PostgreSQL service...
net stop postgresql-x64-18 > nul 2>&1
timeout /t 2 /nobreak > nul
net start postgresql-x64-18 > nul 2>&1
echo [+] PostgreSQL restarted
echo.

REM Step 2: Wait for PostgreSQL to be ready
echo [2/3] Waiting for PostgreSQL to be ready...
timeout /t 3 /nobreak > nul
echo [+] PostgreSQL ready
echo.

REM Step 3: Run Python initialization
echo [3/3] Initializing pgvector extension...
python init_pgvector_windows.py

if errorlevel 1 (
    echo.
    echo [!] Initialization failed. Check error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo pgvector is now ready to use.
echo.
echo Test with:
echo   psql -U postgres -d advia -c "\dx vector"
echo.
pause
