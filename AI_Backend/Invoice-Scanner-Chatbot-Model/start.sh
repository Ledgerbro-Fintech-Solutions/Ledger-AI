#!/bin/bash

echo "Starting Invoice Analysis API..."
echo "Environment variables:"
echo "GROQ_API_KEY: ${GROQ_API_KEY:0:10}..."
echo "HOST: $HOST"
echo "PORT: $PORT"


mkdir -p /app/uploads

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000