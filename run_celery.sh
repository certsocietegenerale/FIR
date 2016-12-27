#!/usr/bin/env sh

sleep 10

celery -A fir_celery.celeryconf worker -l info
