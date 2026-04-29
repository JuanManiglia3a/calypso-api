#!/bin/bash
echo "Iniciando ssh para poder acceder al contenedor por ssh........"
/usr/sbin/sshd &

if [ "$APP_ENV" = "production" ]; then
    echo "Iniciando uvicorn apicalypso en modo $APP_ENV con gunicorn..........."
    NUM_WORKERS=$(nproc)
    echo "Número de workers: $NUM_WORKERS, uno por cada núcleo de CPU"
    exec gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --workers $NUM_WORKERS
else
    echo "Iniciando uvicorn apicalypso en modo desarrollo con uvicorn............"
    exec uvicorn main:app --reload --host 0.0.0.0 --port 5014
fi