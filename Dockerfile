FROM python:3.6-alpine3.6

WORKDIR /root

COPY requirements.txt requirements.txt

RUN apk add --no-cache --virtual .build-deps \
    python3-dev \
    build-base \
    linux-headers \
    pcre-dev && \
    pip install -r requirements.txt

CMD python