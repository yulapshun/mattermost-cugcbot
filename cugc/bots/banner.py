import datetime
import json
import shlex
import time

import cugc.utils.db
import cugc.utils.util


class Banner:
    def __init__(self, app, BANNER_BOT_TOKEN):
        self.app = app
        self.BANNER_BOT_TOKEN = BANNER_BOT_TOKEN

    def run(self, request):
        try:
            # Token from mattermost, unique for each slash command
            token = request.values['token']
            if token == self.BANNER_BOT_TOKEN:
                params = shlex.split(request.values['text'])

                if len(params) == 0:
                    # TODO: Not ideal, should assign an action for this
                    return json.dumps({
                        'response_type': 'ephemeral',
                        'text': self.get_banner(request.values, params)
                    })
                action = params[0]
                response = {
                    'response_type': 'ephemeral',
                    'text': 'Unknown command'
                }

                if action == 'add':
                    response['text'] = self.add_banner(request.values, params)
                elif action == 'view':
                    response['text'] = self.view_banner(request.values, params)
                elif action == 'remove':
                    response['text'] = \
                        self.remove_banner(request.values, params)
                elif action == 'touch':
                    response['text'] = \
                        self.touch_banner(request.values, params)
                elif action == 'help':
                    response['text'] = self.banner_help(request.values, params)
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
            print(e)
            return json.dumps({
                'response_type': 'ephemeral',
                'text': 'Error while executing command'
            })

    # Return json for UI display
    def get_banner(self, body_values, params):
        db = cugc.utils.db.get_db(self.app)
        cur = db.execute(
            'SELECT * FROM banner ORDER BY updated_at DESC LIMIT 3'
        )
        entries = cur.fetchall()
        messages = []
        for entry in entries:
            messages.append({
                'message': entry['content'],
                'created_by': entry['created_by'],
                'updated_at': entry['updated_at']
            })
        return json.dumps(messages)

    def add_banner(self, body_values, params):
        if len(params) < 2:
            return 'No message given'
        created_by = body_values['user_name']
        current_time = int(time.time())
        content = params[1]

        db = cugc.utils.db.get_db(self.app)
        db.execute(
            'INSERT INTO banner (created_by, created_at, updated_at, content) \
            VALUES (:created_by, :created_at, :updated_at, :content)',
            {
                'created_by': created_by,
                'created_at': current_time,
                'updated_at': current_time,
                'content': content
            }
        )
        db.commit()
        return 'Banner successfully added, refresh to see'

    def view_banner(self, body_values, params):
        db = cugc.utils.db.get_db(self.app)
        cur = db.execute('SELECT * FROM banner ORDER BY updated_at DESC')
        entries = cur.fetchall()
        if len(entries) == 0:
            return 'No banner'
        entry_str_arr = []
        for entry in entries:
            created_at = cugc.utils.util.format_timestamp(entry['created_at'])
            updated_at = cugc.utils.util.format_timestamp(entry['created_at'])
            entry_str_arr.append(
                '|' + str(entry['id']) + '|' + entry['content'] + '|' +
                entry['created_by'] + '|' + created_at + '|' + updated_at + '|'
            )
        return """
|Id|Content|Created by|Created at|Updated at|
|:-|:-|:-|:-|:-|
        """ + '\n'.join(entry_str_arr)

    def remove_banner(self, body_values, params):
        if len(params) < 2:
            return 'No banner id given'
        banner_id = params[1]

        db = cugc.utils.db.get_db(self.app)
        cur = db.execute(
            'DELETE FROM banner WHERE id=:banner_id',
            {'banner_id': banner_id}
        )
        db.commit()
        return 'Banner successfully deleted, refresh to see'

    def touch_banner(self, body_values, params):
        if len(params) < 2:
            return 'No banner id given'
        banner_id = params[1]

        db = cugc.utils.db.get_db(self.app)
        cur = db.execute(
            'UPDATE banner SET updated_at=:updated_at WHERE id=:banner_id',
            {'updated_at': int(time.time()), 'banner_id': banner_id}
        )
        db.commit()
        return 'Banner updated time successfully updated, refresh to see'

    def banner_help(self, body_values, params):
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
