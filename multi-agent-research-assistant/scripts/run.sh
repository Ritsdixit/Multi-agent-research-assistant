#!/usr/bin/env bash
# Starts the FastAPI backend and Streamlit frontend together.
set -e

cd "$(dirname "$0")/.."

echo "Starting FastAPI backend on :8000 ..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 2

echo "Starting Streamlit frontend on :8501 ..."
streamlit run frontend/app.py --server.port 8501

kill $BACKEND_PID
