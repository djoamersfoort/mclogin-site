#!/bin/sh

python3 manage.py migrate

exec uvicorn \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level=info \
  --access-log \
  login.asgi:application
