import datetime
import json
import shlex
import time
import requests
from urllib.parse import urljoin

import cugc.utils.db
import cugc.utils.util

class Voting:
    def __init__(self, app, VOTING_BOT_TOKEN):
        self.app = app
        self.VOTING_BOT_TOKEN = VOTING_BOT_TOKEN

    def run(self, request):
        try:
            token = request.values['token']
            if token == self.VOTING_BOT_TOKEN:
                params = shlex.split(request.values['text'])

                if len(params) == 0:
                    return json.dumps({
                        'response_type': 'ephemeral',
                        'text': 'No action given'
                    })
                action = params[0]

                response = {
                    'response_type': 'ephemeral',
                    'text': 'Invalid command'
                }

                if action == 'create':
                    response['response_type'] = 'in_channel'
                    response['text'] = \
                        self.create_vote(request.values, params)
                elif action == 'vote':
                    response['text'] = \
                        self.vote_vote(request.values, params)
                elif action == 'view':
                    response['text'] = \
                        self.view_vote(request.values, params)
                elif action == 'list':
                    response['text'] = \
                        self.list_vote()
                elif action == 'delete':
                    response['text'] = \
                        self.delete_vote(request.values, params)
                elif action == 'help':
                    response['text'] = \
                        self.help_vote()
                return json.dumps(response)
            else:
                return json.dumps({
                    'response_type': 'ephemeral',
                    'text': 'Error while executing command'
                })
        except Exception as e:
            print(e)
            return json.dumps({
                'response_type': 'ephemeral',
                'text': 'Error while executing command'
            })


    def create_vote(self, body_values, params):
        created_by = body_values['user_name']
        created_at = int(time.time())
        vote_name = params[1]
        choice = shlex.split(params[2])

        db = cugc.utils.db.get_db(self.app)
        db.execute(
            'INSERT INTO voting (created_by, created_at, vote_name)'+'VALUES\
             (:created_by, :created_at, :vote_name)',
                {
                    'created_by': '@' + created_by,
                    'created_at': created_at,
                    'vote_name': vote_name
                }
        )
        vote_id = ''
        cur = db.execute('SELECT last_insert_rowid()')
        if cur.fetchone is not None:
            vote_id = cur.fetchone()[0]
            for x in choice:
                db.execute(
                    'INSERT INTO choice (vote_id, choice_name)' + 'VALUES \
                    (:vote_id, :choice_name)',
                    {
                        'vote_id': vote_id,
                        'choice_name': x
                    }
                )
        db.commit()
        cur = db.execute(
            'SELECT * FROM choice WHERE vote_id =:vote_id',
            {'vote_id': vote_id}
        )
        entries = cur.fetchall()
        entry_str_arr = []
        for entry in entries:
            entry_str_arr.append(
                '|{choice_id}|{name}|'.format(
                    choice_id = entry['id'],
                    name = entry['choice_name']
                )
            )
        text = """
Voting created!
Created by: {created_by}
Voting Name: {vote_name}

|Choice ID|Choice name|
|:-|:-|
""".format(
                created_by = '@' + created_by, vote_name = vote_name
            ) + '\n'.join(entry_str_arr)
        return text

    def vote_vote(self, body_values, params):
        if len(params) < 2:
            return 'No message given'
        voted_by = body_values['user_name']
        choice_id = shlex.split(params[1])

        db = cugc.utils.db.get_db(self.app)
        for choice in choice_id:
            cur = db.execute(
                'SELECT * FROM choice WHERE id =:choice_id',
                {'choice_id': choice}
            )
            task_row = cur.fetchone()
            if task_row is not None:
                voter = task_row[3]
                vote_count = task_row[4]
                if voter is None:
                    voter = '@'+ voted_by
                else: voter = voter +' @'+ voted_by
                if vote_count is None:
                    vote_count = 1
                else: vote_count += 1
                db.execute(
                    'UPDATE choice SET voter = :voter, vote_count = :vote_count\
                    WHERE id = :choice',
                    {
                        'voter': voter,
                        'vote_count': vote_count,
                        'choice': choice
                    }
                )
                db.commit()
            else: return 'choice ID not valid'

        return 'Voted successfully! use /vote view to check.'

    def view_vote(self, body_values, params):
        if len(params) < 2:
            return 'No message given'
        vote_id = params[1]
        db = cugc.utils.db.get_db(self.app)
        cur = db.execute(
            'SELECT * FROM choice WHERE vote_id = :vote_id',
            {'vote_id': vote_id}
        )
        entries = cur.fetchall()
        entry_str_arr = []
        for entry in entries:
            entry_str_arr.append(
                '|{id}|{choice_name}|{voter}|{vote_count}|'.format(
                    id = entry['id'],
                    choice_name = entry['choice_name'],
                    voter = entry['voter'],
                    vote_count = entry['vote_count']
                )
            )
        text = '''
|Choice ID|Choice Name|Voters|vote_count|
|:-|:-|:-|:-|
        ''' + '\n'.join(entry_str_arr)
        return text

    def list_vote(self):
        db = cugc.utils.db.get_db(self.app)
        cur = db.execute('SELECT * FROM voting')
        entries = cur.fetchall()
        entry_str_arr = []
        for entry in entries:
            entry_str_arr.append(
                '|{id}|{created_by}|{created_at}|{vote_name}|'.format(
                    id = entry['id'],
                    created_by = entry['created_by'],
                    created_at = cugc.utils.util.format_timestamp(
                        entry['created_at']
                    ),
                    vote_name = entry['vote_name']
                )
            )
        text = '''
|Vote ID|Created by|Time of creation|Vote Name|
|:-|:-|:-|:-|
        ''' + '\n'.join(entry_str_arr)
        return text

    def delete_vote(self, body_values, params):
        db = cugc.utils.db.get_db(self.app)
        delete_id = params[1]
        cur = db.execute(
            'SELECT * FROM choice WHERE id = :delete_id',
            {'delete_id': delete_id}
        )
        delete_row = cur.fetchone()
        vote_count = delete_row['vote_count']
        voter = delete_row['voter']
        voter_arr = shlex.split(voter)
        new_arr = []
        for name in voter_arr:
            if name[1:] == body_values['user_name']:
                vote_count = vote_count - 1
            else:
                new_arr.append(name)
        new_arr = ' '.join(new_arr)
        db.execute(
            'UPDATE choice SET voter = :new_arr, vote_count = :vote_count\
            WHERE id = :delete_id',
            {
                'new_arr': new_arr,
                'vote_count': vote_count,
                'delete_id': delete_id
            }
        )
        db.commit()

        return 'Vote deleted. use /vote view to check.'

    def help_vote(self):
        return"""
## Voting Bot Usage

### 1. Create vote
Create a vote to show at the top command /vote create [vote name] [“option1 option2 option 3”]
e.g. /vote create 你估voting幾時搞掂 "今日 聽日 下世"

Voting created!
Created by: @wingo
Voting Name: 你估voting幾時搞掂

|Choice ID|Choice name|
|:-|:-|
|27|今日|
|28|聽日|
|29|下世|

### 2. List vote
Show all votes in a table and get their vote_id
command /vote list

|Vote ID|Created by|Time of creation|Vote Name|
|:-|:-|:-|:-|
|7|Wingo|2017-07-29|你估voting幾時搞掂
|8|Wai|2017-07-30|幾時行K2


### 3. View choice
Show all choices in a specific vote with the vote_id
Command /vote view [vote_id]
e.g. /vote view 7

|Choice ID|Choice name|Voters|Vote count|
|:-|:-|:-|:-|
|3|今日|Wingo Wai|2
|4|聽日|None|0
|5|下世|None|0


### 4. Vote
Cast a vote with the choice_id
Cammand /vote vote [choice_id]
e.g.
/vote vote "4 5"
or
/vote vote 4
/vote vote 5

|Choice ID|Choice name|Voters|Vote count|
|:-|:-|:-|:-|
|3|今日|Wingo Wai|2
|4|聽日|Wingo|1
|5|下世|Wingo|1


### 5. Delete voted choice
Remove the voted choice with the given choice_id
command /vote delete [option_id]

### 6. Help
Show this message
command /vote help
    """
