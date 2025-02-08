#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found in root directory"
    exit 1
fi

# Create directories if they don't exist
mkdir -p backend/fastapi-oauth2
mkdir -p backend/fastapi-ai-chat

# Copy .env to each service directory
cp .env backend/fastapi-oauth2/
cp .env backend/fastapi-ai-chat/

echo "Successfully copied .env file to all service directories"