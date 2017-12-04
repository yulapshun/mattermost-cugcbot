#!/usr/bin/python3

import os
from configparser import SafeConfigParser

parser = SafeConfigParser()
parser.read('config.ini')

parser.set('banner', 'mattermost_token', os.environ['BANNER_MATTERMOST_TOKEN'])
parser.set('task', 'mattermost_token', os.environ['TASK_MATTERMOST_TOKEN'])
parser.set('voting', 'mattermost_token', os.environ['VOTING_MATTERMOST_TOKEN'])

with open('config.ini', 'w') as configfile:
    parser.write(configfile)


parser.read('uwsgi.ini')
parser.set('uwsgi', 'http-socket', os.environ['UWSGI_HTTP_SOCKET'])
with open('uwsgi.ini', 'w') as configfile:
    parser.write(configfile)
