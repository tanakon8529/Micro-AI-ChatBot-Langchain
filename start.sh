#!/bin/bash

# Parse environment argument
MODE=""
if [ "$1" = "-test" ]; then
    MODE="-d"
fi

# Copy .env files to service directories
echo "Copying .env files to service directories..."
./copy-env.sh

# Start docker compose
echo "Starting docker compose..."
docker compose up --build $MODE