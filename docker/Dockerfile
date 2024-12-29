FROM python:3.8-alpine AS builder
WORKDIR /app
RUN apk add --update git \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    build-base \
    mariadb-dev \
    libffi-dev \
    openldap-dev \
    musl-dev \
    gcc && \
    pip install virtualenv && \
    virtualenv venv && \
    source venv/bin/activate && \
    pip install uwsgitop==0.11 numpy && \
    deactivate

COPY . /app

RUN source venv/bin/activate && \
    find . -name requirements.txt -exec pip install -r {} \; && \
    mv fir/config/installed_apps.txt.sample fir/config/installed_apps.txt && \
    deactivate


FROM python:3.8-alpine AS fir
COPY --from=builder /app /app
RUN apk add libxml2 libxslt mariadb-connector-c libmagic openldap-dev gettext && \
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
