#!/usr/bin/env bash
# T-MEDNet launcher (macOS / Linux)
# Make executable with:  chmod +x run.sh

cd "$(dirname "$0")"

# Activate local venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python main.py
