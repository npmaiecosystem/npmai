#!/bin/bash
set -e

echo "Starting Ollama Server..."
ollama serve &

echo "Waiting for Ollama to start..."
while ! nc -z localhost 11434; do
  sleep 1
done

echo "Pulling LLM model..."
ollama pull llama3.2

echo "Starting FastAPI Application..."
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "${PORT:-7860}"
