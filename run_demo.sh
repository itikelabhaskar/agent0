#!/bin/bash

# AgentX demo script

echo "Starting AgentX demo..."

# Start backend in background
cd backend
python main.py &
BACKEND_PID=$!

# Start frontend
cd ../frontend
streamlit run app.py &
FRONTEND_PID=$!

echo "Demo running. Press Ctrl+C to stop."

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID" INT
wait
