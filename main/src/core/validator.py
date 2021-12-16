import re


illegal_char_filter = re.compile('[^a-zA-Z0-9_-]')


def filter_illegal_char(json_payload: dict):
    # remove illegal characters
    for key, value in json_payload.items():
        if isinstance(value, str):
            json_payload[key] = illegal_char_filter.sub(' ', symbol)
    return json_paylaod