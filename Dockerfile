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
    libxml2 \
    libxml2-dev \
    libxslt \
    libxslt-dev \
    postgresql-dev \

    && rm -rf /var/cache/apk/*

RUN addgroup fir && \
    adduser -D -G fir -s /sbin/nologin fir

WORKDIR /app/FIR

COPY requirements.txt /app/FIR/

RUN pip install -r requirements.txt

#COPY . /app/FIR/

USER fir
ENV HOME /app/FIR
ENV USER fir

#WORKDIR /app/FIR


