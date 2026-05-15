#!/bin/bash
set -e

export OLLAMA_HOST="127.0.0.1:11436" 
taskset -c 0 ollama serve &

export OLLAMA_HOST="127.0.0.1:11435" 
taskset -c 1 ollama serve &

ollama serve &
echo "Waiting for Ollama..."

while ! nc -z localhost 11436 || ! nc -z localhost 11435; do
  sleep 1
done

OLLAMA_HOST="127.0.0.1:11436" ollama pull gemma2:9b
OLLAMA_HOST="127.0.0.1:11435" ollama pull codellama:7b-instruct

echo "Starting FastAPI..."
exec python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}
