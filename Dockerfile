FROM python:3.6-alpine3.6

WORKDIR /root

COPY requirements.txt requirements.txt

RUN apk add --no-cache --virtual .build-deps \
    python3-dev \
    build-base \
    linux-headers \
    pcre-dev && \
    pip install -r requirements.txt

COPY uwsgi.ini /root/uwsgi.ini
COPY config.ini /root/config.ini
COPY cugc /root/cugc

COPY start_up.sh /
COPY init.py /
ENTRYPOINT ["/start_up.sh"]