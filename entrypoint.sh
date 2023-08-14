#!/bin/sh

nohup celery -A fills.tasks worker -l INFO -c 2 &>/dev/null &

uwsgi --ini /app/config/uwsgi.ini