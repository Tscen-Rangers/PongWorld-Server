#!/bin/sh
export DJANGO_SETTINGS_MODULE=pongWorld.config.settings

python manage.py makemigrations
python manage.py migrate

exec python maange.py runserver