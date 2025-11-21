#!/bin/bash
# Quick start script for Deep Research API

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/deep_research"

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Start server
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
