import datetime
import requests
import shlex
import time
from urllib.parse import urljoin
from flask import jsonify

import cugc.utils.db
import cugc.utils.util


class Task:
    def __init__(self, app, TASK_BOT_TOKEN):
        self.app = app
        self.TASK_BOT_TOKEN = TASK_BOT_TOKEN

    def run(self, request):
        try:
            # Token from mattermost, unique for each slash command
            token = request.values['token']
            if token == self.TASK_BOT_TOKEN:
                params = shlex.split(request.values['text'])

                if len(params) == 0:
                    return jsonify({
                        'response_type': 'ephemeral',
                        'text': 'No action given'
                    })
                action = params[0]
                response = {
                    'response_type': 'ephemeral',
                    'text': 'Invalid command'
                }

                if action == 'add':
                    response['response_type'] = 'in_channel'
                    response['text'] = self.add_task(request.values, params)
                elif action == 'view':
                    response['text'] = self.view_task(request.values, params)
                elif action == 'edit':
                    response['text'] = self.edit_task(request.values, params)
                elif action == 'remove':
                    response['text'] = self.remove_task(request.values, params)
                elif action == 'help':
                    response['text'] = self.task_help()
                return jsonify(response)
            else:
                return jsonify({
                    'response_type': 'ephemeral',
                    'text': 'Invalid token'
                })
        except Exception as e:
            print(e)
            return jsonify({
                'response_type': 'ephemeral',
                'text': 'Error while executing command'
            })

    def add_task(self, body_values, params):

        created_by = body_values['user_name']
        current_time = int(time.time())

        title = params[1]
        description = params[2]
        assigned_to = params[3]
        deadline_str = params[4]
        deadline = int(
            datetime.datetime.strptime(deadline_str, '%Y-%m-%d').timestamp()
        )
        # tags_str = params[5]
        # tags = tags_str.split(',')
        tags_str = ''

        db = cugc.utils.db.get_db(self.app)
        db.execute(
            'INSERT INTO task (created_at, updated_at, title, description, \
            assigned_to, created_by,updated_by, deadline, tags)' +
            'VALUES (:created_at, :updated_at, :title, :description, \
            :assigned_to, :created_by, :updated_by, :deadline, :tags)',
            {
                'created_at': current_time,
                'updated_at': current_time,
                'title': title,
                'description': description,
                'assigned_to': assigned_to,
                'created_by': created_by,
                'updated_by': created_by,
                'deadline': deadline,
                'tags': tags_str
            }
        )
        cur = db.execute('SELECT last_insert_rowid()')
        task_id = ''
        task_row = cur.fetchone()
        if task_row is not None:
            task_id = task_row[0]
        db.commit()

        text = """
New task created!
#task{id}

|||
|:-|:-|
|**Title**|{title}|
|**Created by**|{created_by}|
|**Assigned to**|{assigned_to}|
|**description**|{description}|
|**deadline**|{deadline}|
        """.format(
            id=task_id,
            title=title,
            created_by='@' + created_by,
            assigned_to='@' + assigned_to,
            description=description,
            deadline=deadline_str,
            # tags_text=', '.join(['#'+n for n in tags])
        )
        return text

    def view_task(self, body_values, params):
        user_name = params[1]
        db = cugc.utils.db.get_db(self.app)

        if user_name == 'all':
            cur = db.execute('SELECT * FROM task')
        else:
            cur = db.execute(
                'SELECT * FROM task WHERE assigned_to=:assigned_to',
                {'assigned_to': user_name}
            )
        entries = cur.fetchall()
        entry_str_arr = []
        for entry in entries:
            tags = entry['tags'].split(',')
            entry_str_arr.append(
                '|{task_id}|{title}|{description}|{assigned_to}|{deadline}|\
                {updated_by}|{created_by}|{updated_at}|{created_at}|'.format(
                    task_id=entry['id'],
                    title=entry['title'],
                    description=entry['description'],
                    assigned_to='@' + entry['assigned_to'],
                    deadline=cugc.utils.util.format_timestamp(
                        entry['deadline']
                    ),
                    updated_by='@' + entry['updated_by'],
                    created_by='@' + entry['created_by'],
                    updated_at=cugc.utils.util.format_timestamp(
                        entry['updated_at']
                    ),
                    created_at=cugc.utils.util.format_timestamp(
                        entry['created_at']
                    ),
                    # tags=', '.join(['#'+n for n in tags])
                )
            )
        text = """|Id|Title|Description|Assigned to|Deadline|Updated by|Created by|Updated at|Created at|
|:-|:-|:-|:-|:-|:-|:-|:-|
""" + '\n'.join(entry_str_arr)  # noqa
        return text

    def edit_task(self, body_values, params):
        updated_by = body_values['user_name']
        task_id = params[1]
        field = params[2]
        value = params[3]

        if field == 'title':
            db_field = 'title'
        elif field == 'desc':
            db_field = 'description'
        elif field == 'assign':
            db_field = 'assigned_to'
        elif 'deadline':
            db_field = 'deadline'
            value = int(
                datetime.datetime.strptime(value, '%Y-%m-%d').timestamp()
            )

        db = cugc.utils.db.get_db(self.app)
        db.execute(
            'UPDATE task SET {field} = :value, \
            updated_at = :updated_at, updated_by = :updated_by \
            WHERE id = :task_id'.format(field=db_field),
            {
                'updated_at': int(time.time()),
                'updated_by': updated_by,
                'value': value,
                'task_id': task_id
            }
        )
        db.commit()
        return "Task #{id} successfully updated!".format(id=task_id)

    def remove_task(self, body_values, params):
        task_id = params[1]
        db = cugc.utils.db.get_db(self.app)
        cur = db.execute(
            'DELETE FROM task WHERE id=:task_id',
            {'task_id': task_id}
        )
        db.commit()
        return 'Task #{task_id} successfully removed'.format(task_id=task_id)

    def task_help(self):
        return """
## Task Bot Usage

### Add task
Add a task
command `/task add [title] [description] [assign to] [deadline]`
e.g. `/task add 寫文 "Write something" "yulapshun" 2036-12-31`
deadline in the format year-month-day

### View tasks
Show all tasks or tasks assigned to a user
command `/task view [username | all]`
e.g. `/task view yulapshun`

response:

|Id|Title|Description|Assigned to|Deadline|Created by|Created at|Updated at|
|:-|:-|:-|:-|:-|:-|:-|:-|
|1|寫文|Write something|@yulapshun|2036-12-31|@yulapshun|2016-02-02 00:15|2017-02-02 00:31|

### Edit task
Edit a task by its id
command `/task edit [id] [title | desc | assign | deadline] [value]`

Only task title, description, assign to and deadline can be edited
desc = description
assign = assigned to
value is the value you want to update to

e.g. `/task edit 1 title "Do something"`

### Remove task
Remove task
command `/task remove [task id]`

### Help
Show this message
command `/task help`
        """  # noqa
