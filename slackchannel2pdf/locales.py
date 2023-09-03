"""Locales for slackchannel2pdf."""

import datetime as dt
import logging
from typing import Optional

import pytz
from babel import Locale, UnknownLocaleError
from babel.dates import format_date, format_datetime, format_time
from tzlocal import get_localzone

from . import settings

logger = logging.getLogger(__name__)


class LocaleHelper:
    """Helpers for converting date & time according to current locale and timezone"""

    def __init__(
        self,
        my_locale: Optional[Locale] = None,
        my_tz: Optional[pytz.BaseTzInfo] = None,
        author_info: Optional[dict] = None,
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
    def _determine_locale(
        my_locale: Optional[Locale] = None, author_info: Optional[dict] = None
    ) -> Locale:
        if my_locale:
            if not isinstance(my_locale, Locale):
                raise TypeError("my_locale must be a babel Locale object")
            return my_locale

        if author_info:
            try:
                return Locale.parse(author_info["locale"], sep="-")
            except UnknownLocaleError:
                logger.warning("Could not use locale info from Slack.")
                my_locale = None

        try:
            return Locale.default()
        except Exception:
            return Locale.parse(settings.FALLBACK_LOCALE, sep="-")

    @staticmethod
    def _determine_timezone(
        my_tz: Optional[pytz.BaseTzInfo] = None, author_info: Optional[dict] = None
    ) -> pytz.BaseTzInfo:
        if my_tz:
            if not isinstance(my_tz, pytz.BaseTzInfo):
                raise TypeError("my_tz must be of type pytz")
        else:
            if author_info:
                try:
                    my_tz = pytz.timezone(author_info["tz"])
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning("Could not use timezone info from Slack")
                    my_tz = get_localzone()
            else:
                my_tz = get_localzone()
        if not my_tz:
            my_tz = pytz.UTC
        return my_tz

    @property
    def locale(self) -> Locale:
        """Return locale."""
        return self._locale

    @property
    def timezone(self) -> pytz.BaseTzInfo:
        """Return timezone."""
        return self._timezone

    def format_date_full_str(self, my_datetime: dt.datetime) -> str:
        """Return all full formatted date."""
        return format_date(my_datetime, format="full", locale=self.locale)

    def format_datetime_str(self, my_datetime: dt.datetime) -> str:
        """Return formatted datetime string for given dt using locale."""
        return format_datetime(my_datetime, format="short", locale=self.locale)

    def get_datetime_formatted_str(self, timestamp: int) -> str:
        """Return given timestamp as formatted datetime string using locale."""
        my_datetime = self.get_datetime_from_ts(timestamp)
        return format_datetime(my_datetime, format="short", locale=self.locale)

    def get_time_formatted_str(self, timestamp: int) -> str:
        """Return given timestamp as formatted datetime string using locale."""
        my_datetime = self.get_datetime_from_ts(timestamp)
        return format_time(my_datetime, format="short", locale=self.locale)

    def get_datetime_from_ts(self, timestamp: float) -> dt.datetime:
        """Return datetime object of a unix timestamp with local timezone."""
        my_datetime = dt.datetime.fromtimestamp(float(timestamp), pytz.UTC)
        return my_datetime.astimezone(self.timezone)
