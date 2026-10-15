#!/bin/bash
set -e

echo "Waiting for MySQL..."
for i in $(seq 1 30); do
  if python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('$DB_HOST', 3306)); s.close()" 2>/dev/null; then
    echo "MySQL is ready."
    break
  fi
  echo "  attempt $i/30..."
  sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

exec "$@"