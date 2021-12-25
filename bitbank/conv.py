from datetime import datetime


def to_str_by_timestamp(timestamp_millisecond: int):
    return datetime.fromtimestamp(timestamp_millisecond / 1000)
