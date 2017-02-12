import datetime


def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime(
        '%Y-%m-%d %H:%M'
    )
