@echo off
setlocal

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in your PATH.
    pause
    exit /b
)

:: Create the virtual environment
echo Creating virtual environment in 'venv' folder...
py -3.11 -m venv venv

if %ERRORLEVEL% EQU 0 (
    echo venv created successfully.
    
    echo Activating and upgrading pip...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    
    :: Optional: Create an empty requirements file if missing
    if not exist requirements.txt (
        type nul > requirements.txt
        echo Created empty requirements.txt
    )
    
    echo Setup complete!
    call deactivate
) else (
    echo Failed to create virtual environment.
)

pause
