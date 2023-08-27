FROM python:3.11-alpine

COPY requirements.txt /srv/login/requirements.txt

RUN apk update && \
    apk add sqlite && \
    pip install -U pip setuptools && \
    pip install --no-cache-dir -r /srv/login/requirements.txt

WORKDIR /srv
RUN mkdir logs

EXPOSE 8000

COPY login/ /srv/login
COPY manage.py /srv

WORKDIR /srv
COPY start.sh /
ENTRYPOINT ["/start.sh"]
