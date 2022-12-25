#!/bin/sh

echo $ORDER_DB_HOST
echo $ORDER_DB_USERNAME
echo $ORDER_DB_PASSWORD
echo $ORDER_DB_PORT
echo $PGPASSWORD
echo $ORDER_AUTH_DB

#until mongo --authenticationDatabase "$MONGO_AUTH_DB" -host "$MONGO_HOST" -u "$MONGO_USER" -p "$MONGO_PASSWORD" -e 'exit'; do
until psql --host $ORDER_DB_HOST --port $ORDER_DB_PORT --username $ORDER_DB_USERNAME --dbname $ORDER_AUTH_DB; do
  >&2 echo "mongo is unavailable - sleeping" then
  sleep 1
done

echo "Apply flask now"
python3 order.py
exec "$@"
