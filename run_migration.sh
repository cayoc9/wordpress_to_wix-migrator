#!/bin/bash

# This script runs the WordPress to Wix migration tool.

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate venv if present
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

# Ensure dependencies are installed
python3 -m pip install -r requirements.txt >/dev/null 2>&1 || true

# Run the main script
python3 main.py
