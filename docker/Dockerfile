FROM python:3.8-alpine AS builder
WORKDIR /app
COPY . /app
RUN apk add --update git \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    build-base \
    mariadb-dev \
    musl-dev \
    gcc && \
    pip install virtualenv && \
    virtualenv venv && \
    source venv/bin/activate && \
    find . -name requirements.txt -exec pip install -r {} \; && \
    rm -rf .env .git .travis.yml docker Procfile README.md requirements.txt runtime.txt && \
    mv fir/config/installed_apps.txt.sample fir/config/installed_apps.txt && \
    deactivate

FROM python:3.8-alpine AS fir
COPY --from=builder /app /app
RUN apk add libxml2 libxslt mariadb-connector-c && \
    rm -rf /var/cache/apk/* && \
    wget -O /bin/wait-for https://raw.githubusercontent.com/eficode/wait-for/master/wait-for && \
    chmod +x /bin/wait-for

WORKDIR /app/
ENV VIRTUAL_ENV /app/venv
ENV PATH /app/venv/bin:$PATH
ENV HOME /app/
EXPOSE 8000
ENTRYPOINT ["/app/manage.py"]
CMD ["runserver", "--settings", "fir.config.production", "0.0.0.0:8000"]
