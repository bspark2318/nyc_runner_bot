#!/bin/bash

# NYRR Race Scraper - Local Runner
# This script runs the scraper with environment variables from .env file

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    echo "Create a .env file with your credentials (see .env.example)"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the scraper
echo "$(date): Starting NYRR scraper..."
python main.py

# Log the result
if [ $? -eq 0 ]; then
    echo "$(date): Scraper completed successfully"
else
    echo "$(date): Scraper failed with error code $?"
fi
