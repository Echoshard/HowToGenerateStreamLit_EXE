@echo off
REM ==========================================
REM  Streamlit Desktop Environment Setup Script
REM  Author: Chris Castaldi
REM ==========================================

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "REQUIREMENTS_FILE=requirements.txt"
pushd "%SCRIPT_DIR%" >nul 2>&1

REM ==========================================
REM User Configuration
REM ==========================================
set "VENV_NAME=streamlitDesktop"
set "EXE_NAME=MyStreamlitApp.exe"
set "PACKAGES=streamlit"
REM ==========================================

echo.
echo ==========================================
echo Setting up Streamlit Desktop Environment...
echo ==========================================

REM Step 1: Ensure Python and pip are installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found! Please install Python 3.11 or later and retry.
    pause
    popd
    exit /b
)
echo Python found.

REM Step 2: Install virtualenv if not already installed
echo Installing virtualenv...
pip install virtualenv

REM Step 3: Create virtual environment
echo Creating virtual environment "%VENV_NAME%"...
python -m virtualenv "%VENV_NAME%"

REM Step 4: Activate the virtual environment
echo Activating environment...
call ".\%VENV_NAME%\Scripts\activate"

REM Step 5: Install required packages
echo Installing required packages:
echo   %PACKAGES%
pip install %PACKAGES%

REM Step 5b: Install packages from requirements.txt when available
if exist "%SCRIPT_DIR%%REQUIREMENTS_FILE%" (
    echo Installing dependencies from %REQUIREMENTS_FILE%...
    pip install -r "%SCRIPT_DIR%%REQUIREMENTS_FILE%"
) else (
    echo No %REQUIREMENTS_FILE% found in %SCRIPT_DIR%. Skipping optional install.
)

REM Step 6: Copy setup.py and app.py
echo Copying setup.py and app.py into %VENV_NAME% folder...
copy "%SCRIPT_DIR%setup.py" "%SCRIPT_DIR%%VENV_NAME%\"
copy "%SCRIPT_DIR%app.py" "%SCRIPT_DIR%%VENV_NAME%\"

REM Step 7: Navigate to the environment folder
cd "%SCRIPT_DIR%%VENV_NAME%"

REM Step 8: Freeze the application into an executable
echo Building executable with cx_Freeze...
cxfreeze -c setup.py --target-dir toRun --target-name "%EXE_NAME%"

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo Locate your EXE and support files in:
echo   %CD%\toRun
echo.
echo Remember to also include:
echo   - setup.py
echo   - app.py
echo   - Any other Python files your app depends on
echo.
echo This EXE will run any Python app using these packages:
echo   %PACKAGES%
echo ==========================================
pause

popd >nul 2>&1
