import inspect
import os
import unittest
from unittest.mock import patch

import babel
import pytz

import PyPDF2
from slackchannel2pdf import __version__
from slackchannel2pdf import settings
from slackchannel2pdf.channel_exporter import SlackChannelExporter

from .helpers.no_sockets import NoSocketsTestCase
from .helpers.slack_client_stub import SlackClientStub


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

"""
def test_run_with_error(self):
    self.assertRaises(RuntimeError, self.exporter.run(
        ["channel-exporter"],
        "invalid_path"
    ))
"""


@patch("slackchannel2pdf.slack_service.slack")
@patch("slackchannel2pdf.slack_service.sleep", lambda x: None)
class TestSlackChannelExporter(NoSocketsTestCase):
    """New test approach with API mocking, that allows full testing of the exporter"""

    def test_basic(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["C12345678"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])

    def test_run_with_defaults(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["C12345678", "C72345678"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])
        for channel_id in channels:
            self.assertIn(channel_id, response["channels"])
            res_channel = response["channels"][channel_id]
            channel_name = exporter._slack_service.channel_names()[channel_id]
            self.assertEqual(
                res_channel["filename_pdf"],
                os.path.join(
                    currentdir,
                    (exporter._slack_service.team + "_" + channel_name + ".pdf"),
                ),
            )
            self.assertTrue(os.path.isfile(res_channel["filename_pdf"]))

            # assert export details are correct
            self.assertTrue(res_channel["ok"])
            self.assertEqual(res_channel["dest_path"], currentdir)
            self.assertEqual(res_channel["page_format"], "a4")
            self.assertEqual(res_channel["page_orientation"], "portrait")
            self.assertEqual(
                res_channel["max_messages"],
                settings.MAX_MESSAGES_PER_CHANNEL,
            )
            self.assertEqual(res_channel["timezone"], pytz.UTC)
            self.assertEqual(res_channel["locale"], babel.Locale("en", "US"))

            # assert infos in PDF file are correct
            pdf_file = open(res_channel["filename_pdf"], "rb")
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            doc_info = pdf_reader.getDocumentInfo()
            self.assertEqual(doc_info.author, "Erik Kalkoken")
            self.assertEqual(doc_info.creator, f"Channel Export v{__version__}")
            self.assertEqual(
                doc_info.title,
                (exporter._slack_service.team + " / " + channel_name),
            )

    def test_run_with_args_1(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channel = "C72345678"
        # when
        response = exporter.run(
            [channel], currentdir, None, None, "landscape", "a3", 42
        )
        # then
        self.assertTrue(response["ok"])
        self.assertIn(channel, response["channels"])
        res_channel = response["channels"][channel]
        self.assertTrue(res_channel["ok"])
        self.assertEqual(res_channel["message_count"], 5)
        self.assertEqual(res_channel["thread_count"], 0)
        self.assertEqual(res_channel["dest_path"], currentdir)
        self.assertEqual(res_channel["page_format"], "a3")
        self.assertEqual(res_channel["page_orientation"], "landscape")
        self.assertEqual(res_channel["max_messages"], 42)

    def test_all_message_variants(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["G1234567X"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])

    def test_should_handle_team_name_with_invalid_characters(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T92345678")
        exporter = SlackChannelExporter("TOKEN_DUMMY")
        channels = ["C12345678"]
        # when
        response = exporter.run(channels, currentdir)
        # then
        self.assertTrue(response["ok"])

    def test_should_use_given_timezone(self, mock_slack):
        # given
        mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
        exporter = SlackChannelExporter(
            slack_token="TOKEN_DUMMY",
            my_tz=pytz.timezone("Asia/Bangkok"),
            my_locale=babel.Locale.parse("es-MX", sep="-"),
        )
        channel = "C12345678"
        # when
        response = exporter.run([channel], currentdir)
        # then
        self.assertTrue(response["ok"])
        res_channel = response["channels"][channel]
        self.assertTrue(res_channel["ok"])
        self.assertEqual(
            res_channel["timezone"],
            pytz.timezone("Asia/Bangkok"),
        )
        self.assertEqual(res_channel["locale"], babel.Locale.parse("es-MX", sep="-"))


class TestTransformations(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
            cls.exporter = SlackChannelExporter("TOKEN_DUMMY")

    def test_transform_text_user(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<@U62345678>", True),
            "<b>@Janet Hakuli</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<@U999999999>", True),
            "<b>@user_U999999999</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<@W999999999>", True),
            "<b>@user_W999999999</b>",
        )

    def test_transform_text_channel(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<#C72345678>", True),
            "<b>#london</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<#C55555555>", True),
            "<b>#channel_C55555555</b>",
        )

    def test_transform_text_usergroup(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<!subteam^S72345678>", True),
            "<b>@marketing</b>",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text("<!subteam^SAZ94GDB8>", True),
            "<b>@usergroup_SAZ94GDB8</b>",
        )

    def test_transform_text_special(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("<!everyone>", True),
            "<b>@everyone</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!here>", True), "<b>@here</b>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!channel>", True),
            "<b>@channel</b>",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "<!date^1392734382^Posted {date_num} {time_secs}"
                "|Posted 2014-02-18 6:39:42 AM PST>",
                True,
            ),
            self.exporter._locale_helper.get_datetime_formatted_str(1392734382),
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<!xyz>", True),
            "<b>@special_xyz</b>",
        )

    def test_transform_text_url(self):
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "<https://www.google.com|Google>", True
            ),
            '<a href="https://www.google.com">Google</a>',
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("<https://www.google.com>", True),
            '<a href="https://www.google.com">https://www.google.com</a>',
        )

    def test_transform_text_formatting(self):
        self.assertEqual(
            self.exporter._transformer.transform_text("*bold*", True), "<b>bold</b>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("_italic_", True), "<i>italic</i>"
        )
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "text *bold* text _italic_ text", True
            ),
            "text <b>bold</b> text <i>italic</i> text",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("`code`", True),
            '<s fontfamily="NotoSansMono">code</s>',
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("*_bold+italic_*", True),
            "<b><i>bold+italic</i></b>",
        )

    def test_transform_text_general(self):
        self.assertEqual(
            self.exporter._transformer.transform_text(
                "some *text* <@U62345678> more text", True
            ),
            "some <b>text</b> <b>@Janet Hakuli</b> more text",
        )
        self.assertEqual(
            self.exporter._transformer.transform_text("first\nsecond\nthird", True),
            "first<br>second<br>third",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text(
                "some text <@U62345678> more text", True
            ),
            "some text <b>@Janet Hakuli</b> more text",
        )

        self.assertEqual(
            self.exporter._transformer.transform_text(
                "before ident\n>indented text\nafter ident", True
            ),
            "before ident<br><blockquote>indented text</blockquote><br>after ident",
        )


class TestOther(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with patch("slackchannel2pdf.slack_service.slack") as mock_slack:
            mock_slack.WebClient.return_value = SlackClientStub(team="T12345678")
            cls.exporter = SlackChannelExporter("TOKEN_DUMMY")


if __name__ == "__main__":
    unittest.main()
