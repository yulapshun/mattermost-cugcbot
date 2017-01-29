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

app = Flask(__name__)
app.config.from_object(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, config['main']['cugc_db'])
    # DATABASE=os.path.join(app.root_path, 'data/cugc.db')
))

BANNER_BOT_TOKEN = config['main']['banner_bot_token']

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def test():
    return 'It\'s working!!!'

@app.route('/banner', methods=['POST'])
def banner():
    token = request.values['token']
    if token == BANNER_BOT_TOKEN:
        params = shlex.split(request.values['text'])

        if len(params) == 0:
            return json.dumps({
                'response_type': 'ephemeral',
                'text': get_banner(request.values, params)
            })
        action = params[0]
        response = {
            'response_type': 'ephemeral',
            'text': 'banner added'
        }

        if action == 'add':
            response['text'] = add_banner(request.values, params)
        elif action == 'view':
            response['text'] = view_banner(request.values, params)
        elif action == 'remove':
            response['text'] = remove_banner(request.values, params)
        elif action == 'help':
            response['text'] = banner_help(request.values, params)
        else:
            response = {
                'response_type': 'ephemeral',
                'text': 'Invalid command'
            }
        return json.dumps(response)

def get_banner(body_values, params):
    db = get_db()
    cur = db.execute('SELECT * FROM banner ORDER BY updated_at DESC')
    entries = cur.fetchall()
    messages = []
    for entry in entries:
        messages.append({
            'message': entry['content'],
            'updated_at': entry['updated_at']
        })
    return json.dumps(messages)

def add_banner(body_values, params):

    current_time = int(time.time())
    content = params[1]

    db = get_db()
    db.execute(
        'INSERT INTO banner (created_at, updated_at, content)' +
        'VALUES (:created_at, :updated_at, :content)',
        {
            'created_at': current_time,
            'updated_at': current_time,
            'content': content
        }
    )
    db.commit();
    return 'Banner successfully added, refresh to see'

def view_banner(body_values, params):
    db = get_db()
    cur = db.execute('SELECT * FROM banner ORDER BY updated_at')
    entries = cur.fetchall()
    entry_str_arr = []
    for entry in entries:
        created_at = datetime.datetime.fromtimestamp(entry['created_at']).strftime('%Y-%m-%d %H:%M')
        updated_at = datetime.datetime.fromtimestamp(entry['created_at']).strftime('%Y-%m-%d %H:%M')
        entry_str_arr.append('|'+str(entry['id'])+'|'+entry['content']+'|'+created_at+'|'+updated_at+'|')
    return """
|Id|Content|Created at|Updated at|
|:-|:-|:-|:-|
    """ + '\n'.join(entry_str_arr)

def remove_banner(body_values, params):
    banner_id = params[1]

    db = get_db()
    cur = db.execute('DELETE FROM banner WHERE id=:banner_id', {'banner_id': banner_id})
    db.commit()
    return 'Banner successfully deleted, refresh to see'

def banner_help(body_values, params):
    return """
## Banner Bot Usage

### Add banner
Add a banner to show at the top
command `/banner add [quoted banner content]`
e.g. `/banner add "Happy new year!"`

### View banners
Show all banners in a table
command `/banner view`

response:

|Id|Content|Created at|Updated at|
|:-|:-|:-|:-|
|1|Merry Christmas!|2016-12-25 00:15|2017-12-25 00:31|
|2|Happy new year!|2017-01-29 10:22|2017-01-29 10:22|

### Remove banner
Remove the banner with the given id
command `/banner remove 1`

### Help
Show this message
command `/banner help`
    """

if __name__ == "__main__":
    with app.app_context():
        init_db()
        app.run()
