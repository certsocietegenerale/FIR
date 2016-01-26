# Dockerfile for FIR development instance
# written by Kyle Maxwell
# build with the command:
#
# sudo docker build -t fir .
# sudo docker run -it -p 8000:8000 fir
#
# then access http://localhost:8000 in your browser

#MAINTAINER Kyle Maxwell, krmaxwell@gmail.com
FROM ubuntu:14.04
RUN apt-get update && \
  apt-get dist-upgrade -y
RUN apt-get install -y --no-install-recommends \
  python-pip  \
  python-dev \
  python-lxml \
  python-virtualenv \
  libxml2-dev \
  libxslt1-dev \
  libz-dev \
  build-essential \
  git && \

  groupadd -r fir && \
  useradd -r -g fir -d /home/fir -s /sbin/nologin -c "FIR user" fir

WORKDIR /home
RUN git clone https://github.com/certsocietegenerale/FIR.git && \
  mv /home/FIR /home/fir && \
  chown -R fir:fir /home/fir && \
  cd fir && \
  pip install -r requirements.txt

USER fir
ENV HOME /home/fir
ENV USER fir
WORKDIR /home/fir
RUN ./manage.py migrate && \
    ./manage.py loaddata incidents/fixtures/seed_data.json && \
    ./manage.py loaddata incidents/fixtures/dev_users.json
EXPOSE 8000
ENTRYPOINT ["/home/fir/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]
