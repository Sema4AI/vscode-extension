@echo off

SET scriptPath=%~dp0
SET scriptPath=%scriptPath:~0,-1%
cd /D %scriptPath%
SET venvDir=venv

:: Get RCC, binary with which we're going to create the master environment.
SET rccUrl=https://downloads.robocorp.com/rcc/releases/v18.1.5/windows64/rcc.exe
IF NOT EXIST ".\rcc.exe" (
    curl -o rcc.exe %rccUrl% --fail || goto venv_error
)

:: Create a new or replace an already existing virtual environment.
IF EXIST "%scriptPath%\%venvDir%" (
    echo Detected existing development environment.
    echo Do you want to create a clean environment? [Y/N]
    choice /C YN /N /M "Select [Y]es (clean environment) or [N]o (use existing):"
    IF ERRORLEVEL 2 GOTO venv_setup
)

:venv_new
echo Creating a clean environment...
%scriptPath%\rcc.exe venv %scriptPath%\development-environment.yaml --space sema4ai-vscode-development --force --sema4ai

:venv_setup
:: Activate the virtual environment and install dependencies everytime.
call .\%venvDir%\Scripts\activate.bat
python -m pip install poetry==1.8.3

cd /D %scriptPath%\..

yarn install
poetry install
code .\.vscode\sema4ai-code.code-workspace || goto vscode_error
goto end

:venv_error
echo.
echo Development environment setup failed!
goto end

:vscode_error
echo.
echo Running VSCode failed!
goto end

:end
pause
