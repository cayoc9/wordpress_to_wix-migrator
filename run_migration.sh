#!/bin/bash

# This script runs the WordPress to Wix migration tool.

# Navigate to the project directory
cd "$(dirname "$0")"

# Run the main script
./.venv/bin/python main.py
