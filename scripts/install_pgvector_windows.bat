@echo off
REM Windows pgvector Installation Script
REM This script helps install pgvector v0.8.1 on Windows PostgreSQL

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  pgvector Installation for Windows
echo ========================================
echo.

REM Check if PostgreSQL is installed
echo [*] Checking for PostgreSQL installation...
for /f "tokens=*" %%A in ('where pg_config 2^>nul') do set PG_CONFIG=%%A

if not defined PG_CONFIG (
    echo [!] PostgreSQL not found in PATH
    echo.
    echo Please ensure PostgreSQL is installed and in your PATH
    echo Or set PGROOT environment variable:
    echo   set PGROOT=C:\Program Files\PostgreSQL\18
    echo.
    exit /b 1
)

echo [+] Found PostgreSQL at: %PG_CONFIG%

REM Get PostgreSQL version
for /f "tokens=*" %%A in ('pg_config --version 2^>nul') do set PG_VERSION=%%A
echo [+] Version: %PG_VERSION%

REM Get PostgreSQL directories
for /f "tokens=*" %%A in ('pg_config --pkglibdir 2^>nul') do set PKGLIB=%%A
for /f "tokens=*" %%A in ('pg_config --includedir 2^>nul') do set PGINCLUDE=%%A
for /f "tokens=*" %%A in ('pg_config --includedir-server 2^>nul') do set PGINCLUDE_SERVER=%%A

echo [+] Library directory: %PKGLIB%
echo [+] Include directory: %PGINCLUDE%
echo.

REM Check if git is installed
echo [*] Checking for git...
for /f "tokens=*" %%A in ('where git 2^>nul') do set GIT_PATH=%%A

if not defined GIT_PATH (
    echo [!] git not found in PATH
    echo    Please install git or add it to your PATH
    exit /b 1
)

echo [+] Git found: %GIT_PATH%
echo.

REM Clone and build pgvector
echo [*] Building pgvector v0.8.1...
cd /d %TEMP%

if exist pgvector (
    echo [*] Removing existing pgvector directory...
    rmdir /s /q pgvector
)

echo [*] Cloning pgvector repository...
git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git

if errorlevel 1 (
    echo [!] Failed to clone pgvector
    exit /b 1
)

cd pgvector

REM Check for nmake
echo [*] Checking for nmake...
for /f "tokens=*" %%A in ('where nmake 2^>nul') do set NMAKE_PATH=%%A

if not defined NMAKE_PATH (
    echo [!] nmake not found. Installing Visual C++ build tools...
    echo     You can download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    exit /b 1
)

echo [+] nmake found: %NMAKE_PATH%
echo.

REM Build with specific configuration
echo [*] Building pgvector...
nmake /F Makefile.win

if errorlevel 1 (
    echo [!] Build failed
    exit /b 1
)

echo [+] Build successful
echo.

REM Install
echo [*] Installing pgvector to PostgreSQL...
nmake /F Makefile.win install

if errorlevel 1 (
    echo [!] Installation failed
    exit /b 1
)

echo [+] Installation successful
echo.

REM Verify installation
echo [*] Verifying installation...
if exist "%PKGLIB%\vector.dll" (
    echo [+] vector.dll found at: %PKGLIB%\vector.dll
) else (
    echo [!] vector.dll not found at: %PKGLIB%\vector.dll
)

if exist "%PKGLIB%\vector.control" (
    echo [+] vector.control found at: %PKGLIB%\vector.control
) else (
    echo [!] vector.control not found at: %PKGLIB%\vector.control
)

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart PostgreSQL service:
echo    net stop postgresql-x64-18
echo    net start postgresql-x64-18
echo.
echo 2. Enable the extension in your database:
echo    psql -U postgres -d your_database
echo    CREATE EXTENSION IF NOT EXISTS vector;
echo.
echo 3. Verify with:
echo    \dx vector
echo.
pause
