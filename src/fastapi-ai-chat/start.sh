#!/bin/bash

# Exit on error
set -e

# Debug information
echo "Starting FastAPI service..."
echo "Current working directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# Handle environment file setup
if [ -f /.env ]; then
    echo "Copying .env from root to /app/service/.env"
    cp /.env /app/service/.env
    chmod 600 /app/service/.env
elif [ -f .env ] && [ "$(pwd)" != "/app/service" ]; then
    echo "Using local .env file for development"
    cp .env /app/service/.env
    chmod 600 /app/service/.env
fi

# Add shared modules to Python path
export PYTHONPATH="${PYTHONPATH}:/app/service"

# Use the environment variable or default to 80
PORT=${PORT_FASTAPI_AI_CHAT:-80}
echo "Using port: $PORT"

# Start Gunicorn with the environment variable
echo "Starting Gunicorn..."
exec gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --bind "0.0.0.0:$PORT" \
    --access-logfile - \
    --error-logfile - \
    --log-level debug