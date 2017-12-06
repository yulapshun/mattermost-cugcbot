#!/bin/sh

python /init.py
uwsgi --ini uwsgi.ini
