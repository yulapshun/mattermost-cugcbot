from flask import g
import sqlite3

def connect_db(app):
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db(app):
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db(app)
    return g.sqlite_db
