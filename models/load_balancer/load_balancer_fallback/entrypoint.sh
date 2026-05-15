#!/bin/bash
set -e

echo "Initialising Load Balancer of NPMAI LLM"
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "${PORT:-7860}"
