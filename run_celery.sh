#!/usr/bin/env sh

sleep 20

celery -A fir_celery.celeryconf worker -l info
