# Dockerfile for FIR development instance
# written by Robert Haist
#
# Mostly based on the ubuntu image by Kyle Maxwell
#
# build with the command:
#
# sudo docker build -t fir .
# sudo docker run -it -p 8000:8000 fir
#
# then access http://localhost:8000 in your browser

# MAINTAINER Robert Haist, SleuthKid@mailbox.org
FROM alpine:3.4

RUN apk add --update \
    python \
    python-dev \
    py-pip \
    build-base \
    git \
    libxml2 \
    libxml2-dev \
    libxslt \
    libxslt-dev \
    postgresql-dev \

    && rm -rf /var/cache/apk/*

RUN addgroup fir && \
    adduser -D -G fir -s /sbin/nologin fir

WORKDIR /app

RUN git clone https://github.com/certsocietegenerale/FIR.git && \
    chown -R fir:fir /app/FIR && \
    cd FIR && \
    pip install -r requirements.txt && \
    cp fir/config/installed_apps.txt.sample fir/config/installed_apps.txt

USER fir
ENV HOME /app/FIR
ENV USER fir

WORKDIR /app/FIR

RUN ./manage.py migrate && \
    ./manage.py loaddata incidents/fixtures/seed_data.json && \
    ./manage.py loaddata incidents/fixtures/dev_users.json

EXPOSE 8000
ENTRYPOINT ["/app/FIR/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
