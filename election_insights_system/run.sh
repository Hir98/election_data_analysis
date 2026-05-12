#!/usr/bin/env bash
# Convenience script: generate data, start backend + frontend.
set -e

python scripts/generate_sample_data.py

# Start FastAPI in the background
uvicorn backend.app:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Give backend a moment to come up
sleep 2

# Start Streamlit (foreground)
streamlit run frontend/Home.py

# Stop backend on exit
kill $BACKEND_PID
