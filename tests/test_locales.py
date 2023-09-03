from unittest import TestCase
from unittest.mock import patch

from babel import Locale

from slackchannel2pdf.locales import LocaleHelper

MODULE_PATH = "slackchannel2pdf.locales"


class TestDetermineLocale(TestCase):
    def test_should_use_locale_when_provided_1(self):
        # given
        locale = Locale("en", "US")
        # when
        result = LocaleHelper._determine_locale(locale)
        # then
        self.assertEqual(result, locale)

    def test_should_use_locale_when_provided_2(self):
        # given
        locale = Locale("en", "US")
        author_info = {"locale": "de-DE"}
        # when
        result = LocaleHelper._determine_locale(locale, author_info)
        # then
        self.assertEqual(result, locale)

    def test_should_use_auth_info(self):
        # given
        author_info = {"locale": "de-DE"}
        # when
        result = LocaleHelper._determine_locale(None, author_info)
        # then
        self.assertEqual(result, Locale("de", "DE"))

    def test_should_return_default_when_nothing_provided(self):
        # when
        with patch(MODULE_PATH + ".Locale", wraps=Locale) as spy:
            LocaleHelper._determine_locale()
            # then
            self.assertTrue(spy.default.called)

    def test_should_return_default_when_parsing_fails(self):
        # given
        author_info = {"locale": "xx-yy"}
        # when
        with patch(MODULE_PATH + ".Locale", wraps=Locale) as spy:
            LocaleHelper._determine_locale(None, author_info)
            # then
            self.assertTrue(spy.default.called)

    def test_should_return_fallback_when_default_fails(self):
        # when
        with patch(MODULE_PATH + ".settings") as mock_settings:
            mock_settings.FALLBACK_LOCALE = "de-DE"
            with patch(MODULE_PATH + ".Locale.default") as mock:
                mock.side_effect = RuntimeError
                result = LocaleHelper._determine_locale()
                # then
            self.assertEqual(result, Locale("de", "DE"))
