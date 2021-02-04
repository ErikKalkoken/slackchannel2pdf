import datetime as dt
import unittest
from unittest.mock import patch

import babel
import pytz
from tzlocal import get_localzone

from slackchannel2pdf import helpers
from slackchannel2pdf.locales import LocaleHelper


class TestTransformEncoding(unittest.TestCase):
    def test_should_transform_special_chars(self):
        self.assertEqual(helpers.transform_encoding("special char ✓"), "special char ✓")
        self.assertEqual(helpers.transform_encoding("&lt;"), "<")
        self.assertEqual(helpers.transform_encoding("&#60;"), "<")


class TestLocaleHelper(unittest.TestCase):
    def test_should_init_with_defaults(self):
        # when
        locale_helper = LocaleHelper()
        # then
        self.assertEqual(locale_helper.locale, babel.Locale.default())
        self.assertEqual(locale_helper.timezone, get_localzone())

    def test_should_use_given_locale_and_timezone(self):
        # given
        my_locale = babel.Locale.parse("es-MX", sep="-")
        my_tz = pytz.timezone("Asia/Bangkok")
        # when
        locale_helper = LocaleHelper(my_locale=my_locale, my_tz=my_tz)
        # then
        self.assertEqual(locale_helper.locale, my_locale)
        self.assertEqual(locale_helper.timezone, my_tz)

    def test_should_use_locale_and_timezone_from_slack(self):
        # given
        author_info = {"locale": "es-MX", "tz": "Asia/Bangkok"}
        # when
        locale_helper = LocaleHelper(author_info=author_info)
        # then
        self.assertEqual(locale_helper.locale, babel.Locale.parse("es-MX", sep="-"))
        self.assertEqual(locale_helper.timezone, pytz.timezone("Asia/Bangkok"))

    def test_should_use_fallback_locale_if_none_can_be_determined(self):
        # when
        with patch("slackchannel2pdf.locales.Locale.default") as mock_default:
            mock_default.return_value = None
            locale_helper = LocaleHelper()
        # then
        self.assertEqual(locale_helper.locale, babel.Locale.parse("en"))

    def test_should_use_fallback_timezone_if_none_can_be_determined(self):
        # when
        with patch("slackchannel2pdf.locales.get_localzone") as mock_get_localzone:
            mock_get_localzone.return_value = None
            locale_helper = LocaleHelper()
        # then
        self.assertEqual(locale_helper.timezone, pytz.UTC)

    def test_should_convert_epoch_to_datetime(self):
        # given
        locale_helper = LocaleHelper()
        ts = 1006300923
        # when
        my_datetime = locale_helper.get_datetime_from_ts(ts)
        # then
        self.assertEqual(my_datetime.timestamp(), ts)

    def test_should_format_datetime(self):
        # given
        locale_helper = LocaleHelper(my_locale=babel.Locale.parse("de-DE", sep="-"))
        # when
        my_datetime = dt.datetime(2021, 2, 3, 18, 10)
        result = locale_helper.format_datetime_str(my_datetime)
        # then
        self.assertEqual(result, "03.02.21, 18:10")

    def test_should_format_epoch(self):
        # given
        locale_helper = LocaleHelper(my_locale=babel.Locale.parse("de-DE", sep="-"))
        # when
        my_datetime = dt.datetime(2021, 2, 3, 18, 10)
        result = locale_helper.get_datetime_formatted_str(my_datetime.timestamp())
        # then
        self.assertEqual(result, "03.02.21, 18:10")
