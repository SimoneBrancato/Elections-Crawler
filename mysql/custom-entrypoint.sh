#!/bin/bash
set -e

# Avvia MySQL in background
/usr/local/bin/docker-entrypoint.sh mysqld &

# Attendi che MySQL sia pronto
until mysqladmin ping -h "127.0.0.1" --silent; do
  echo "Waiting for MySQL..."
  sleep 5
done

echo "Initializing database..."
mysql -u root -proot < /docker-entrypoint-initdb.d/init.sql

wait
