#!/usr/bin/env bash
# Run the API server from the backend directory so uvicorn can find api_server.
cd "$(dirname "$0")"
exec uvicorn api_server:app --reload --port 8000 "$@"
