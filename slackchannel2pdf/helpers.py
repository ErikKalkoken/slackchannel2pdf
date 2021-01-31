import datetime as dt
import html
import json
import os

from babel.dates import format_datetime, format_time
import pytz


def transform_encoding(text):
    """adjust encoding to latin-1 and transform HTML entities"""
    text2 = html.unescape(text)
    text2 = text2.encode("utf-8", "replace").decode("utf-8")
    text2 = text2.replace("\t", "    ")
    return text2


def read_array_from_json_file(filename, quiet=False):
    """reads a json file and returns its contents as array"""
    filename += ".json"
    if not os.path.isfile(filename):
        if quiet is False:
            print(f"WARN: file does not exist: {filename}")
        arr = list()
    else:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                arr = json.load(f)
        except Exception as e:
            if quiet is False:
                print(f"WARN: failed to read from {filename}: ", e)
            arr = list()

    return arr


def write_array_to_json_file(arr, filename):
    """writes array to a json file"""
    filename += ".json"
    print(f"Writing file: name {filename}")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(arr, f, sort_keys=True, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: failed to write to {filename}: ", e)


class LocaleHelper:
    """Helpers for converting date & time according to current locale and timezone"""

    def __init__(self, locale, timezone) -> None:
        self._locale = locale
        self._timezone = timezone

    @property
    def locale(self):
        return self._locale

    @property
    def timezone(self):
        return self._timezone

    def format_datetime_str(self, dt):
        """returns formated datetime string for given dt using locale"""
        return format_datetime(dt, format="short", locale=self.locale)

    def get_datetime_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        dt = self.get_datetime_from_ts(ts)
        return format_datetime(dt, format="short", locale=self.locale)

    def get_time_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        dt = self.get_datetime_from_ts(ts)
        return format_time(dt, format="short", locale=self.locale)

    def get_datetime_from_ts(self, ts):
        """returns datetime object of a unix timestamp with local timezone"""
        my_dt = dt.datetime.fromtimestamp(float(ts), pytz.UTC)
        return my_dt.astimezone(self.timezone)
