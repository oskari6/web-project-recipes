#!/bin/bash
set -e

# Create virtual environment only if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
fi

.venv/bin/pip install -r requirements.txt
echo "Dependencies installed."

# Generate local secrets
if [ ! -f ".env" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "SECRET_KEY=$SECRET_KEY" > .env
    echo "Secret session key generated to .env."
fi

echo "Setup complete."