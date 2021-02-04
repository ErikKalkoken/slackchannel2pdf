import datetime as dt
import html
import json
from pathlib import Path

from babel import Locale, UnknownLocaleError
from babel.dates import format_datetime, format_time, format_date
import pytz
from tzlocal import get_localzone

from . import settings


def transform_encoding(text):
    """adjust encoding to latin-1 and transform HTML entities"""
    text2 = html.unescape(text)
    text2 = text2.encode("utf-8", "replace").decode("utf-8")
    text2 = text2.replace("\t", "    ")
    return text2


def read_array_from_json_file(filepath: Path, quiet=False):
    """reads a json file and returns its contents as array"""
    my_file = filepath.parent / (filepath.name + ".json")
    if not my_file.is_file:
        if quiet is False:
            print(f"WARN: file does not exist: {filepath}")
        arr = list()
    else:
        try:
            with my_file.open("r", encoding="utf-8") as f:
                arr = json.load(f)
        except IOError as e:
            if quiet is False:
                print(f"WARN: failed to read from {my_file}: ", e)
            arr = list()

    return arr


def write_array_to_json_file(arr, filepath: Path):
    """writes array to a json file"""
    my_file = filepath.parent / (filepath.name + ".json")
    print(f"Writing file: name {filepath}")
    try:
        with my_file.open("w", encoding="utf-8") as f:
            json.dump(arr, f, sort_keys=True, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"ERROR: failed to write to {my_file}: ", e)


class LocaleHelper:
    """Helpers for converting date & time according to current locale and timezone"""

    def __init__(
        self,
        my_locale: Locale = None,
        my_tz: pytz.BaseTzInfo = None,
        author_info: dict = None,
    ) -> None:
        """
        Args:
        - my_locale: Primary locale to use
        - my_tz: Primary timezone to use
        - author_info: locale and timezone to use from this Slack response
        if my_locale and/or my_tz are not given
        """
        self._locale = self._determine_locale(my_locale, author_info)
        self._timezone = self._determine_timezone(my_tz, author_info)

    @staticmethod
    def _determine_locale(my_locale: Locale = None, author_info: dict = None) -> Locale:
        if my_locale:
            if not isinstance(my_locale, Locale):
                raise TypeError("my_locale must be a babel Locale object")
        else:
            if author_info:
                try:
                    my_locale = Locale.parse(author_info["locale"], sep="-")
                except UnknownLocaleError:
                    print("WARN: Could not use locale info from Slack")
                    my_locale = Locale.default()
            else:
                my_locale = Locale.default()
        if not my_locale:
            my_locale = Locale.parse(settings.FALLBACK_LOCALE)
        return my_locale

    @staticmethod
    def _determine_timezone(
        my_tz: pytz.BaseTzInfo = None, author_info: dict = None
    ) -> pytz.BaseTzInfo:
        if my_tz:
            if not isinstance(my_tz, pytz.BaseTzInfo):
                raise TypeError("my_tz must be of type pytz")
        else:
            if author_info:
                try:
                    my_tz = pytz.timezone(author_info["tz"])
                except pytz.exceptions.UnknownTimeZoneError:
                    print("WARN: Could not use timezone info from Slack")
                    my_tz = get_localzone()
            else:
                my_tz = get_localzone()
        if not my_tz:
            my_tz = pytz.UTC
        return my_tz

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

    def print_locale(self) -> None:
        """prints current locale"""
        print(f"Locale is: {self.locale.get_display_name()} [{self.locale}]")

    def print_timezone(self) -> None:
        """prints current timezone"""
        print(f"Timezone is: {str(self.timezone)}")
