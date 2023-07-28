#!/bin/sh

uwsgi --http :4200 --wsgi-file /app/fillexcel/wsgi.py