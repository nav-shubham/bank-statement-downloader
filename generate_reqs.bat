@echo off
setlocal

:: Check if the venv folder and activation script exist
if not exist "venv\Scripts\activate.bat" (
    echo Error: 'venv' folder or activation script not found in this directory.
    pause
    exit /b
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Generating requirements.txt...
pip freeze > requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo requirements.txt created successfully!
) else (
    echo Failed to create requirements.txt.
)

:: Deactivate and finish
call deactivate
pause
