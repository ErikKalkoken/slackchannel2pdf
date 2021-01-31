import datetime as dt
import html

from babel.dates import format_datetime, format_time
import pytz


def transform_encoding(text):
    """adjust encoding to latin-1 and transform HTML entities"""
    text2 = html.unescape(text)
    text2 = text2.encode("utf-8", "replace").decode("utf-8")
    text2 = text2.replace("\t", "    ")
    return text2


class LocaleHelper:
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
