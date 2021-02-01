import datetime as dt
import html
import json
import os

from babel import Locale, UnknownLocaleError
from babel.dates import format_datetime, format_time, format_date
import pytz
from tzlocal import get_localzone


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
        except IOError as e:
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
    except IOError as e:
        print(f"ERROR: failed to write to {filename}: ", e)


class LocaleHelper:
    """Helpers for converting date & time according to current locale and timezone"""

    def __init__(self, my_locale, my_tz, author_info) -> None:
        # set locale
        # check if overridden locale is valid
        if my_locale is not None:
            if not isinstance(my_locale, Locale):
                raise TypeError("my_locale must be a babel Locale object")
        else:
            # if not overridden use timezone info from author on Slack if available
            if author_info:
                try:
                    my_locale = Locale.parse(author_info["locale"], sep="-")
                except UnknownLocaleError:
                    print("WARN: Could not use locale info from Slack")
                    my_locale = Locale.default()

            # else use local time of this system
            else:
                my_locale = Locale.default()

        print(f"Locale is: {my_locale.get_display_name()} [{my_locale}]")
        self._locale = my_locale

        # set timezone
        # check if overridden timezone is valid
        if my_tz is not None:
            if not isinstance(my_tz, pytz.BaseTzInfo):
                raise TypeError("my_tz must be of type pytz")
        else:
            # if not overridden use timezone info from author on Slack if available
            if author_info:
                try:
                    my_tz = pytz.timezone(author_info["tz"])
                except pytz.exceptions.UnknownTimeZoneError:
                    print("WARN: Could not use timezone info from Slack")
                    my_tz = get_localzone()
            # else use local time of this system
            else:
                my_tz = get_localzone()

        print(f"Timezone is: {str(my_tz)}")
        self._timezone = my_tz

    @property
    def locale(self):
        return self._locale

    @property
    def timezone(self):
        return self._timezone

    def format_date_full_str(self, my_datetime):
        return format_date(my_datetime, format="full", locale=self.locale)

    def format_datetime_str(self, my_datetime):
        """returns formated datetime string for given dt using locale"""
        return format_datetime(my_datetime, format="short", locale=self.locale)

    def get_datetime_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        my_datetime = self.get_datetime_from_ts(ts)
        return format_datetime(my_datetime, format="short", locale=self.locale)

    def get_time_formatted_str(self, ts):
        """return given timestamp as formated datetime string using locale"""
        my_datetime = self.get_datetime_from_ts(ts)
        return format_time(my_datetime, format="short", locale=self.locale)

    def get_datetime_from_ts(self, ts):
        """returns datetime object of a unix timestamp with local timezone"""
        my_datetime = dt.datetime.fromtimestamp(float(ts), pytz.UTC)
        return my_datetime.astimezone(self.timezone)
