#!/usr/bin/bash

envsubst '$PORT' < ./nginx.conf > /tmp/nginx.conf
uvicorn web.backend.main:app --host 127.0.0.1 --port 8000 &
nginx -c /tmp/nginx.conf -g "daemon off;"