#!/usr/bin/env bash

python manage.py migrate

python manage.py makemigrations fills

python manage.py sqlmigrate fills 0001

python manage.py shell

python manage.py createsuperuser

python manage.py runserver 4200
