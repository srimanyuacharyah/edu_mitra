@echo off
echo Starting FastAPI Backend...
start cmd /k "uvicorn src.backend.main:app --reload --port 8000"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak > NUL

echo Starting New Unified Frontend...
start cmd /k "cd src\frontend && python -m http.server 3000"

echo Both services started!
