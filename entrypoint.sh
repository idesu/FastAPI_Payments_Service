#!/bin/bash
set -e

# Запуск FastAPI (Uvicorn)
if [ "$SERVICE_TYPE" = "api" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
elif [ "$SERVICE_TYPE" = "consumer" ]; then
    exec faststream run app.consumer:app --workers $WORKERS_COUNT
elif [ "$SERVICE_TYPE" = "outbox_worker" ]; then
    exec python -m app.outbox_worker
elif [ "$SERVICE_TYPE" = "migration" ]; then
    exec alembic upgrade head
else
    echo "Unknown SERVICE_TYPE: $SERVICE_TYPE"
    exit 1
fi