#!/usr/bin/env sh

sleep 10

celery -A fir worker -l info
