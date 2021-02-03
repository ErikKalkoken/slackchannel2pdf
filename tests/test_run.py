from argparse import Namespace

from unittest import TestCase
from unittest.mock import patch

from slackchannel2pdf.run import main


@patch("slackchannel2pdf.run.SlackChannelExporter")
@patch("slackchannel2pdf.run.parse_args")
class TestRun(TestCase):
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
            token="token",
            timezone=None,
            write_raw_data=None,
        )
        # when
        main()
        # then
        self.assertTrue(MockExporter.called)
        kwargs = MockExporter.call_args[1]
        self.assertEqual(kwargs["slack_token"], "token")
        self.assertTrue(MockExporter.return_value.run.called)
        kwargs = MockExporter.return_value.run.call_args[1]
        self.assertEqual(kwargs["channel_inputs"], "channel")
