#!/bin/bash
cd "$(dirname "$0")"
pip install -q -r requirements.txt --break-system-packages 2>/dev/null
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8077}
