"""Helper functions for DSDA command line client"""

import operator
import requests

from datetime import timedelta
from lxml import html


def get_web_page_html(web_page_url):
    """Generic method to get HTML text from URL"""
    page = requests.get(web_page_url)
    return html.fromstring(page.content)


def sort_file(file_to_sort):
    """Generic method to get HTML text from URL"""
    with open(file_to_sort) as file_to_sort_stream:
        lines = file_to_sort_stream.readlines()
    lines.sort()
    with open(file_to_sort, 'w') as file_to_sort_stream_sorted:
        for line in lines:
            file_to_sort_stream_sorted.write(line)


def total_time(time_list):
    """Helper function to calculate total time from time list"""
    _total_time = timedelta()
    for demo_time in time_list:
        _total_time += demo_time

    return _total_time


def average_time(time_list):
    """Helper function to calculate average time from time list"""
    _total_time = 0
    count = 0
    for demo_time in time_list:
        _total_time += demo_time.total_seconds()
        count += 1
    if count:
        average_time_in_seconds = _total_time / count
    else:
        average_time_in_seconds = 0

    return timedelta(seconds=average_time_in_seconds)


def longest_time(time_list):
    """Helper function to calculate longest time from time list"""
    _longest_time = None
    for demo_time in time_list:
        if _longest_time:
            if demo_time > _longest_time:
                _longest_time = demo_time
        else:
            _longest_time = demo_time

    return _longest_time


def max_tuple_dict(tuple_dict, key_index):
    """Calculates the maximum of a dict of tuples

    Uses the element at key_index as the key for comparisons.
    In case of an empty dict, this returns (None, None).
    """
    if len(tuple_dict):
        return max(tuple_dict.items(), key=operator.itemgetter(key_index))
    else:
        return None, None


def format_timedelta(timedelta_obj):
    """Helper function to format timedelta to a human-readable time string"""
    if timedelta_obj:
        timedelta_string = '%02d:%02d:%02d' % (
            int(timedelta_obj.total_seconds() // 3600),
            (timedelta_obj.seconds // 60) % 60,
            timedelta_obj.seconds % 60
        )

        return timedelta_string

    return None


def str_to_timedelta(time_string):
    """Helper function to convert a time string to a timedelta"""
    if time_string:
        time_components = time_string.split(':')
        if len(time_components) == 3:
            demo_time = timedelta(
                hours=int(time_components[0]),
                minutes=int(time_components[1]),
                seconds=int(time_components[2])
            )
        else:
            demo_time = timedelta(
                0,
                minutes=int(time_components[0]),
                seconds=int(time_components[1])
            )

        return demo_time

    return None
