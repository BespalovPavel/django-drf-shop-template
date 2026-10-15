#!/bin/sh
set -e

echo "Ожидание запуска PostgreSQL..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"