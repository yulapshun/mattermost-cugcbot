import configparser
import datetime
import json
import os
import requests
import shlex
import sqlite3
import time
from urllib.parse import urljoin
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from cugc.bots import banner, task
import cugc.utils.db

app = Flask(__name__)
app.config.from_object(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, config['main']['cugc_db'])
))

BANNER_BOT_TOKEN = config['banner']['mattermost_token']
TASK_BOT_TOKEN = config['task']['mattermost_token']

banner_bot = cugc.bots.banner.Banner(app, BANNER_BOT_TOKEN)
task_bot = cugc.bots.task.Task(app, TASK_BOT_TOKEN)

def init_db():
    db = cugc.utils.db.get_db(app)
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# For testing server is up and responding
@app.route('/')
def test():
    return 'It\'s working!!!'

@app.route('/banner', methods=['POST'])
def banner():
    return banner_bot.run(request)

@app.route('/task', methods=['POST'])
def task():
    return task_bot.run(request)

with app.app_context():
    init_db()
