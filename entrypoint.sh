#!/bin/sh

nohup celery -A fills.tasks worker -l INFO -c 2 &>/app/logs/celery-console.log &

uwsgi --ini /app/config/uwsgi.ini