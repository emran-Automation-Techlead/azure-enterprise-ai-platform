#!/bin/bash
# FastAPI backend (internal, port 8000) + Streamlit UI (public, port 8501) in one container.
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_URL=http://localhost:8000 exec streamlit run ui/streamlit_app.py \
  --server.port 8501 --server.address 0.0.0.0 --server.headless true
