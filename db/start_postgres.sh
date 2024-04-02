#!/bin/sh

if [ -f ./pongWorld/.env ]; then
    export $(cat ./pongWorld/.env | sed 's/#.*//g' | xargs)
fi

psql -U postgres -c "CREATE DATABASE $DB_NAME;"
psql -U postgres -d $DB_NAME -c "\connect $DB_NAME;"
psql -U postgres -d $DB_NAME -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' SUPERUSER;"
psql -U postgres -d $DB_NAME -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf-8';"
psql -U postgres -d $DB_NAME -c "ALTER ROLE $DB_USER SET timezone TO 'Asia/Seoul';"
psql -U postgres -d $DB_NAME -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
