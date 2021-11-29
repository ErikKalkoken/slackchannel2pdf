import datetime as dt
from argparse import Namespace
from unittest import TestCase
from unittest.mock import patch

import babel
import pytz

from slackchannel2pdf.cli import main


@patch("slackchannel2pdf.cli.SlackChannelExporter")
@patch("slackchannel2pdf.cli.parse_args")
class TestCli(TestCase):
    def test_should_start_export_for_channel(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel="channel",
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
            quiet=False,
        )
        # when
        main()
        # then
        self.assertTrue(MockExporter.called)
        kwargs = MockExporter.call_args[1]
        self.assertEqual(kwargs["slack_token"], "DUMMY_TOKEN")
        self.assertTrue(MockExporter.return_value.run.called)
        kwargs = MockExporter.return_value.run.call_args[1]
        self.assertEqual(kwargs["channel_inputs"], "channel")

    def test_should_use_token_from_environment_var(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel="channel",
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token=None,
            timezone=None,
            write_raw_data=None,
            quiet=False,
        )
        # when
        with patch("slackchannel2pdf.cli.os") as mock_os:
            mock_os.environ = {"SLACK_TOKEN": "DUMMY_TOKEN"}
            main()
        # then
        self.assertTrue(MockExporter.called)
        kwargs = MockExporter.call_args[1]
        self.assertEqual(kwargs["slack_token"], "DUMMY_TOKEN")

    def test_should_show_version_and_abort(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token=None,
            timezone=None,
            version=True,
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()

    def test_should_abort_when_no_token_given(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token=None,
            timezone=None,
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()

    def test_should_use_given_timezone(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone="Asia/Bangkok",
            write_raw_data=None,
            quiet=False,
        )
        # when
        main()
        # then
        self.assertTrue(MockExporter.called)
        kwargs = MockExporter.call_args[1]
        self.assertEqual(kwargs["my_tz"], pytz.timezone("Asia/Bangkok"))

    def test_should_use_given_locale(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale="es-MX",
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
            quiet=False,
        )
        # when
        main()
        # then
        self.assertTrue(MockExporter.called)
        kwargs = MockExporter.call_args[1]
        self.assertEqual(kwargs["my_locale"], babel.Locale.parse("es-MX", sep="-"))

    def test_should_use_given_oldest_and_latest(self, mock_parse_args, MockExporter):
        # given
        latest = "2020-03-03 22:00"
        oldest = "2020-02-02 20:00"
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=latest,
            locale=None,
            max_messages=None,
            oldest=oldest,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
            quiet=False,
        )
        # when
        main()
        # then
        self.assertTrue(MockExporter.called)
        mock_run = MockExporter.return_value.run
        self.assertTrue(mock_run.called)
        kwargs = mock_run.call_args[1]
        self.assertEqual(kwargs["oldest"], dt.datetime(2020, 2, 2, 20, 0))
        self.assertEqual(kwargs["latest"], dt.datetime(2020, 3, 3, 22, 0))

    def test_should_abort_if_locale_is_invalid(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale="xx",
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()

    def test_should_abort_if_timezone_is_invalid(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone="xx",
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()

    def test_should_abort_if_oldest_is_invalid(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest=None,
            locale=None,
            max_messages=None,
            oldest="xx",
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()

    def test_should_abort_if_latest_is_invalid(self, mock_parse_args, MockExporter):
        # given
        mock_parse_args.return_value = Namespace(
            add_debug_info=False,
            channel=None,
            destination=None,
            latest="xx",
            locale=None,
            max_messages=None,
            oldest=None,
            page_format=None,
            page_orientation=None,
            token="DUMMY_TOKEN",
            timezone=None,
            write_raw_data=None,
        )
        # when
        with self.assertRaises(SystemExit):
            main()
