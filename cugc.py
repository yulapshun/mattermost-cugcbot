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

# For testing server is up and responding
@app.route('/')
def test():
    return 'It\'s working!!!'

# TODO: separate each command into module
@app.route('/banner', methods=['POST'])
def banner():
    try:
        # Token from mattermost, unique for each slash command
        token = request.values['token']
        if token == BANNER_BOT_TOKEN:
            params = shlex.split(request.values['text'])

            if len(params) == 0:
                # TODO: Not ideal, should assign an action for this
                return json.dumps({
                    'response_type': 'ephemeral',
                    'text': get_banner(request.values, params)
                })
            action = params[0]
            response = {
                'response_type': 'ephemeral',
                'text': 'Unknown command'
            }

            if action == 'add':
                response['text'] = add_banner(request.values, params)
            elif action == 'view':
                response['text'] = view_banner(request.values, params)
            elif action == 'remove':
                response['text'] = remove_banner(request.values, params)
            elif action == 'touch':
                response['text'] = touch_banner(request.values, params)
            elif action == 'help':
                response['text'] = banner_help(request.values, params)
            else:
                response = {
                    'response_type': 'ephemeral',
                    'text': 'Invalid command'
                }
            return json.dumps(response)
        else:
            return json.dumps({
                'response_type': 'ephemeral',
                'text': 'Invalid token'
            })
    except Exception as e:
        print(e.message)
        return json.dumps({
            'response_type': 'ephemeral',
            'text': 'Error while executing command'
        })

# Return json for UI display
def get_banner(body_values, params):
    db = get_db()
    cur = db.execute('SELECT * FROM banner ORDER BY updated_at DESC LIMIT 3')
    entries = cur.fetchall()
    messages = []
    for entry in entries:
        messages.append({
            'message': entry['content'],
            'created_by': entry['created_by'],
            'updated_at': entry['updated_at']
        })
    return json.dumps(messages)

def add_banner(body_values, params):
    if len(params) < 2:
        return 'No message given'
    created_by = body_values['user_name']
    current_time = int(time.time())
    content = params[1]

    db = get_db()
    db.execute(
        'INSERT INTO banner (created_by, created_at, updated_at, content)' +
        'VALUES (:created_by, :created_at, :updated_at, :content)',
        {
            'created_by': created_by,
            'created_at': current_time,
            'updated_at': current_time,
            'content': content
        }
    )
    db.commit();
    return 'Banner successfully added, refresh to see'

def view_banner(body_values, params):
    db = get_db()
    cur = db.execute('SELECT * FROM banner ORDER BY updated_at DESC')
    entries = cur.fetchall()
    if len(entries) == 0:
        return 'No banner'
    entry_str_arr = []
    for entry in entries:
        created_at = datetime.datetime.fromtimestamp(entry['created_at']).strftime('%Y-%m-%d %H:%M')
        updated_at = datetime.datetime.fromtimestamp(entry['created_at']).strftime('%Y-%m-%d %H:%M')
        entry_str_arr.append('|'+str(entry['id'])+'|'+entry['content']+'|'+entry['created_by']+'|'+created_at+'|'+updated_at+'|')
    return """
|Id|Content|Created by|Created at|Updated at|
|:-|:-|:-|:-|:-|
    """ + '\n'.join(entry_str_arr)

def remove_banner(body_values, params):
    if len(params) < 2:
        return 'No banner id given'
    banner_id = params[1]

    db = get_db()
    cur = db.execute('DELETE FROM banner WHERE id=:banner_id', {'banner_id': banner_id})
    db.commit()
    return 'Banner successfully deleted, refresh to see'

def touch_banner(body_values, params):
    if len(params) < 2:
        return 'No banner id given'
    banner_id = params[1]

    db = get_db()
    cur = db.execute('UPDATE banner SET updated_at=:updated_at WHERE id=:banner_id', {'updated_at': int(time.time()),'banner_id': banner_id})
    db.commit()
    return 'Banner updated time successfully updated, refresh to see'

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
command `/banner remove [banner_id]`

### Put banner at the top
Update updated at time of a banner
command `/banner touch [banner_id]`

### Help
Show this message
command `/banner help`
    """

with app.app_context():
    init_db()
