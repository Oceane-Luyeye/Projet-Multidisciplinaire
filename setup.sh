#!/bin/bash

set -e
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

echo "Creating new virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Upgrading pip..."
"$VENV_DIR/bin/pip" install --upgrade pip

if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    "$VENV_DIR/bin/pip" install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi

echo "Virtual environment setup complete."
echo "To activate, run: source $VENV_DIR/bin/activate"