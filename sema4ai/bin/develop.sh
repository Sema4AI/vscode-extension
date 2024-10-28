#!/bin/bash -e

# Navigate to the script's directory
cd "$(dirname "$0")"

# Define the virtual environment directory name
venvDir=venv  # Naming it differently from Poetry's ".venv" to avoid conflicts

# Check if the script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "Activating an already existing virtual environment."
    source "../$venvDir/bin/activate"
    return  # Stop the rest of the script without exiting the shell
fi

# Download RCC binary if it does not exist
if [ ! -f rcc ]; then
    system=$(uname -s)
    case ${system} in
        Linux*)     url=https://downloads.robocorp.com/rcc/releases/v18.5.0/linux64/rcc;;
        Darwin*)    url=https://downloads.robocorp.com/rcc/releases/v18.5.0/macos64/rcc;;
        *)          echo "Invalid platform '$system' detected!"; exit 1;;
    esac
    curl -o rcc $url
    chmod +x rcc
fi

# Check if the virtual environment directory exists
if [ -d "$venvDir" ]; then
    echo "Detected existing development environment."
    read -r -p "Do you want to create a clean environment? [Y/N] " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Replacing existing environment with a clean one..."
        ./rcc venv development-environment.yaml --space robocorp-development --force --sema4ai
    else
        echo "Using existing development environment."
    fi
else
    echo "Creating a new environment..."
    ./rcc venv development-environment.yaml --space robocorp-development --force --sema4ai
fi

# Activate the virtual environment
source "./$venvDir/bin/activate"

# Install dependencies
python -m pip install poetry==1.8.3

# Move up one directory to the project root
cd ..
yarn install
poetry install

# Open the workspace in VS Code
code ./.vscode/sema4ai-code.code-workspace || {
    echo "Running VSCode failed!"
    exit 1
}

echo "Setup completed successfully."
echo "To activate the environment, source this script: source $(basename "$0")"
