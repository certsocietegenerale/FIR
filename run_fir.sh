#!/usr/bin/env sh

#cp fir/config/installed_apps.txt.sample fir/config/installed_apps.txt

./manage.py migrate

./manage.py loaddata incidents/fixtures/seed_data.json && \
    ./manage.py loaddata incidents/fixtures/dev_users.json

./manage.py runserver 0.0.0.0:8000
