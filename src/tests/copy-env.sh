#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if .env file exists in project root
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    printf "Error: .env file not found in project root directory\n"
    exit 1
fi


# Copy .env to each service directory
cp "$PROJECT_ROOT/.env" "$PROJECT_ROOT/src/tests/"

printf "Successfully copied .env file to all service directories\n"
