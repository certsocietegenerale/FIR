#!/usr/bin/env sh

sleep 15

celery -A fir_celery.celeryconf worker -l info
